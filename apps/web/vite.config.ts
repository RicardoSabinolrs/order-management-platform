import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
// `defineConfig` vem do vitest para tipar o bloco `test`; `loadEnv` e `Plugin`
// so existem no pacote do vite.
import { loadEnv, type Plugin } from 'vite'
import { defineConfig } from 'vitest/config'

// O .env fica na raiz do monorepo, nao em apps/web: um arquivo so configura
// backend e frontend. Sem isto, o Vite procuraria em apps/ e nunca acharia.
const ENV_DIR = fileURLToPath(new URL('../..', import.meta.url))

const API_PATHS = ['/api', '/health']

function isApiRequest(url: string | undefined): boolean {
  return API_PATHS.some((prefix) => url?.startsWith(prefix) ?? false)
}

/**
 * Fecha o modo de demonstracao no servidor de dev.
 *
 * Com os mocks ligados nao ha backend do outro lado. Se uma requisicao de API
 * escapar do MSW, o proxy tentaria conectar e devolveria `ECONNREFUSED` - um
 * erro que nao diz nada sobre a causa. Este middleware responde antes do
 * proxy, dizendo exatamente qual rota escapou e o que fazer.
 */
function mockModeGuard(useMocks: boolean): Plugin {
  return {
    name: 'oms:mock-mode-guard',
    configureServer(server) {
      const modo = useMocks
        ? 'dados de demonstracao (VITE_USE_MOCKS=true)'
        : 'API real (VITE_USE_MOCKS=false)'
      server.httpServer?.once('listening', () => {
        server.config.logger.info(`  \x1b[33m➜\x1b[0m  modo:    ${modo}`)
      })

      if (!useMocks) return

      server.middlewares.use((req, res, next) => {
        if (!isApiRequest(req.url)) return next()

        const rota = `${req.method ?? 'GET'} ${req.url ?? ''}`
        server.config.logger.warn(
          `[mocks] ${rota} escapou do MSW. Recarregue a pagina; se persistir, ` +
            'falta um handler em src/mocks/handlers.ts.',
        )
        res.statusCode = 501
        res.setHeader('Content-Type', 'application/problem+json')
        res.end(
          JSON.stringify({
            type: 'about:blank#mock_nao_interceptado',
            title: 'Requisicao nao interceptada pelo MSW',
            status: 501,
            code: 'mock_nao_interceptado',
            detail:
              `A aplicacao esta em modo de demonstracao e ${rota} nao foi interceptada. ` +
              'Recarregue a pagina para o service worker assumir o controle, ou rode ' +
              'com VITE_USE_MOCKS=false para usar a API real.',
            instance: req.url,
          }),
        )
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  // Prefixo vazio carrega tambem as variaveis sem VITE_ (o alvo do proxy).
  // Isto roda apenas no processo do Vite: nada daqui vai para o bundle.
  const env = loadEnv(mode, ENV_DIR, '')
  const useMocks = env.VITE_USE_MOCKS === 'true' || env.VITE_USE_MOCKS === '1'
  const proxyTarget = env.API_PROXY_TARGET || 'http://localhost:8000'

  return {
    envDir: ENV_DIR,
    plugins: [react(), mockModeGuard(useMocks)],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5173,
      host: true,
      // Sem proxy no modo de demonstracao: nao ha backend para encaminhar, e
      // o guard acima ja responde por estas rotas.
      proxy: useMocks
        ? undefined
        : {
            // O front fala com a API pelo mesmo origin: sem CORS e sem URL
            // absoluta espalhada pelo codigo.
            '/api': { target: proxyTarget, changeOrigin: true },
            '/health': { target: proxyTarget, changeOrigin: true },
          },
    },
    test: {
      globals: true,
      environment: 'happy-dom',
      restoreMocks: true,
      setupFiles: ['./src/test/setup.ts'],
      // A suite nao pode herdar o .env da maquina: com envDir na raiz, quem
      // trocasse VITE_USE_MOCKS veria testes quebrarem sem mexer em codigo.
      // O MSW e ligado sempre pelo setup; quem precisa do modo de
      // demonstracao troca `config` com `vi.mock`.
      env: { VITE_USE_MOCKS: '', VITE_API_BASE_URL: '' },
    },
  }
})
