/**
 * Credenciais do operador padrao.
 *
 * Vivem aqui, e nao em `mocks/`, porque a tela de login precisa delas para
 * preencher o formulario no modo de demonstracao - e importar de `mocks/`
 * arrastaria os dados falsos para o bundle de producao.
 *
 * Sao as mesmas do backend recem-instalado (`SECURITY_OPERATOR_*`), entao
 * servem tanto com MSW quanto com a API real em ambiente local.
 */
export const DEMO_CREDENTIALS = {
  email: 'operador@sabinolabs.dev',
  password: 'demo1234',
} as const
