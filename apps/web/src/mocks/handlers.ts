/**
 * Handlers do MSW.
 *
 * Reproduzem o contrato real da API, incluindo os erros em `problem+json`.
 * Interceptam na camada de rede, entao o codigo da aplicacao faz `fetch` de
 * verdade e nao sabe que esta falando com um mock.
 */

import { delay, http, HttpResponse } from 'msw'

import { DEMO_USER, orders, products, stock, users, type MockUser } from '@/mocks/data'
import { config } from '@/shared/config/env'
import type { OrderDTO, OrderStatusDTO, ProductDTO, UserDTO } from '@/shared/api/types'

const LATENCY_MS = 200

/**
 * Casa o caminho com a mesma base que o cliente HTTP usa.
 *
 * Com `VITE_API_BASE_URL` preenchido o app chama URL absoluta; um handler
 * registrado em caminho relativo deixaria de casar e o mock falharia em
 * silencio, parecendo erro de rede.
 */
const url = (path: string) => `${config.apiBaseUrl}${path}`

const TRANSICOES: Record<OrderStatusDTO, OrderStatusDTO[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
}

function problem(status: number, code: string, detail: string, extra: object = {}) {
  return HttpResponse.json(
    { type: `about:blank#${code}`, title: code, status, detail, code, instance: '', ...extra },
    { status, headers: { 'Content-Type': 'application/problem+json' } },
  )
}

function unauthorized() {
  return problem(401, 'unauthenticated', 'Credencial ausente.')
}

function forbidden() {
  return problem(403, 'permissao_negada', 'Apenas administradores podem gerenciar usuarios.')
}

function unhandled(request: Request) {
  const { method } = request
  const { pathname } = new URL(request.url)
  console.error(`[mocks] sem handler para ${method} ${pathname}`)
  return problem(
    501,
    'mock_nao_implementado',
    `O modo de demonstracao nao tem um handler para ${method} ${pathname}. ` +
      'Adicione-o em src/mocks/handlers.ts ou rode com VITE_USE_MOCKS=false.',
  )
}

function authorized(request: Request): boolean {
  return request.headers.get('Authorization')?.startsWith('Bearer ') ?? false
}

/**
 * O token do mock carrega o id do usuario: `mock.access.token` e o operador
 * padrao, `mock.access.token.<id>` e qualquer outro. Assim o perfil de quem
 * chama decide o que o handler permite, como na API real.
 */
function tokenFor(user: UserDTO): string {
  return user.id === DEMO_USER.id ? 'mock.access.token' : `mock.access.token.${user.id}`
}

function currentUser(request: Request): MockUser | undefined {
  const token = request.headers.get('Authorization')?.replace(/^Bearer /, '')
  if (!token?.startsWith('mock.access.token')) return undefined
  const id = token === 'mock.access.token' ? DEMO_USER.id : token.slice('mock.access.token.'.length)
  return users.find((user) => user.id === id)
}

function publicUser(user: MockUser): UserDTO {
  const { id, name, email, role, avatar_url } = user
  return { id, name, email, role, avatar_url }
}

function paginate<ItemT>(items: ItemT[], url: URL) {
  const page = Number(url.searchParams.get('page') ?? '1')
  const pageSize = Number(url.searchParams.get('page_size') ?? '10')
  const start = (page - 1) * pageSize
  return { items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize }
}

function balanceOf(productId: string) {
  return stock.find((entry) => entry.product_id === productId)
}

function recompute(productId: string) {
  const balance = balanceOf(productId)
  if (balance) balance.quantity_available = balance.quantity_on_hand - balance.quantity_reserved
}

export const handlers = [
  // -- autenticacao ---------------------------------------------------------
  http.post(url('/api/v1/auth/login'), async ({ request }) => {
    await delay(LATENCY_MS)
    const body = (await request.json()) as { email?: string; password?: string }
    const user = users.find((candidate) => candidate.email === body.email?.trim().toLowerCase())

    if (!user || user.password !== body.password) {
      return problem(401, 'unauthenticated', 'E-mail ou senha incorretos.')
    }

    return HttpResponse.json({
      access_token: tokenFor(user),
      token_type: 'bearer',
      expires_in: 1800,
      user: publicUser(user),
    })
  }),

  http.get(url('/api/v1/auth/me'), async ({ request }) => {
    await delay(50)
    const user = currentUser(request)
    return user ? HttpResponse.json(publicUser(user)) : unauthorized()
  }),

  // -- usuarios -------------------------------------------------------------
  http.get(url('/api/v1/users'), async ({ request }) => {
    await delay(LATENCY_MS)
    const user = currentUser(request)
    if (!user) return unauthorized()
    if (user.role !== 'admin') return forbidden()
    return HttpResponse.json(paginate(users.map(publicUser), new URL(request.url)))
  }),

  http.post(url('/api/v1/users'), async ({ request }) => {
    await delay(LATENCY_MS)
    const user = currentUser(request)
    if (!user) return unauthorized()
    if (user.role !== 'admin') return forbidden()

    const body = (await request.json()) as {
      name: string
      email: string
      password: string
      role: UserDTO['role']
    }
    const email = body.email.trim().toLowerCase()
    if (users.some((candidate) => candidate.email === email)) {
      return problem(409, 'email_ja_cadastrado', `Ja existe um usuario com o e-mail ${email}.`)
    }

    const created: MockUser = {
      id: `usr_${String(users.length + 1).padStart(4, '0')}`,
      name: body.name.trim(),
      email,
      role: body.role,
      avatar_url: null,
      password: body.password,
    }
    users.push(created)
    return HttpResponse.json(publicUser(created), { status: 201 })
  }),

  // -- produtos -------------------------------------------------------------
  http.get(url('/api/v1/products'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const url = new URL(request.url)
    const search = (url.searchParams.get('search') ?? '').toLowerCase()
    const active = url.searchParams.get('active')

    let found = products
    if (active !== null) found = found.filter((p) => String(p.active) === active)
    if (search) {
      found = found.filter(
        (p) => p.name.toLowerCase().includes(search) || p.sku.toLowerCase().includes(search),
      )
    }

    return HttpResponse.json(paginate(found, url))
  }),

  http.post(url('/api/v1/products'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const body = (await request.json()) as Record<string, string | number>
    const sku = String(body.sku).trim().toUpperCase()

    if (products.some((p) => p.sku === sku)) {
      return problem(409, 'duplicate_sku', `Ja existe um produto com o SKU ${sku}.`)
    }

    const now = new Date().toISOString()
    const created: ProductDTO = {
      id: `prd_${Math.random().toString(36).slice(2, 10)}`,
      sku,
      name: String(body.name),
      description: String(body.description ?? ''),
      price_in_cents: Number(body.price_in_cents),
      currency: 'BRL',
      active: true,
      created_at: now,
      updated_at: now,
    }
    products.unshift(created)

    const quantidade = Number(body.initial_stock ?? 0)
    stock.unshift({
      product_id: created.id,
      sku,
      quantity_on_hand: quantidade,
      quantity_reserved: 0,
      quantity_available: quantidade,
      updated_at: now,
    })

    return HttpResponse.json(created, { status: 201 })
  }),

  http.patch(url('/api/v1/products/:productId'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const product = products.find((p) => p.id === params.productId)
    if (!product) return problem(404, 'entity_not_found', 'Produto nao encontrado.')

    const body = (await request.json()) as Partial<ProductDTO>
    Object.assign(product, body, { updated_at: new Date().toISOString() })
    return HttpResponse.json(product)
  }),

  http.delete(url('/api/v1/products/:productId'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const index = products.findIndex((p) => p.id === params.productId)
    if (index < 0) return problem(404, 'entity_not_found', 'Produto nao encontrado.')

    const balance = balanceOf(String(params.productId))
    if (balance && balance.quantity_reserved > 0) {
      return problem(
        409,
        'business_rule_violation',
        `O produto tem ${balance.quantity_reserved} unidade(s) reservada(s). Desative-o.`,
      )
    }

    products.splice(index, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // -- estoque --------------------------------------------------------------
  http.get(url('/api/v1/stock'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()
    return HttpResponse.json(paginate(stock, new URL(request.url)))
  }),

  http.post(url('/api/v1/stock/:productId/receipts'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const balance = balanceOf(String(params.productId))
    if (!balance) return problem(404, 'entity_not_found', 'Estoque nao encontrado.')

    const body = (await request.json()) as { quantity: number }
    balance.quantity_on_hand += body.quantity
    balance.updated_at = new Date().toISOString()
    recompute(balance.product_id)
    return HttpResponse.json(balance)
  }),

  http.post(url('/api/v1/stock/:productId/adjustments'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const balance = balanceOf(String(params.productId))
    if (!balance) return problem(404, 'entity_not_found', 'Estoque nao encontrado.')

    const body = (await request.json()) as { quantity_on_hand: number; reason: string }
    if (body.quantity_on_hand < balance.quantity_reserved) {
      return problem(
        409,
        'business_rule_violation',
        `Ha ${balance.quantity_reserved} unidade(s) reservada(s): o saldo nao pode ficar abaixo disso.`,
      )
    }

    balance.quantity_on_hand = body.quantity_on_hand
    balance.updated_at = new Date().toISOString()
    recompute(balance.product_id)
    return HttpResponse.json(balance)
  }),

  // -- pedidos --------------------------------------------------------------
  http.get(url('/api/v1/orders'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    const search = (url.searchParams.get('search') ?? '').toLowerCase()

    let found = orders
    if (status) found = found.filter((order) => order.status === status)
    if (search) {
      found = found.filter(
        (order) =>
          order.reference.toLowerCase().includes(search) ||
          order.customer.name.toLowerCase().includes(search),
      )
    }

    const page = paginate(found, url)
    return HttpResponse.json({
      ...page,
      items: page.items.map((order) => ({
        id: order.id,
        reference: order.reference,
        status: order.status,
        customer_name: order.customer.name,
        item_count: order.items.reduce((total, item) => total + item.quantity, 0),
        total_in_cents: order.total_in_cents,
        placed_at: order.placed_at,
      })),
    })
  }),

  http.get(url('/api/v1/orders/:orderId'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const order = orders.find((candidate) => candidate.id === params.orderId)
    return order
      ? HttpResponse.json(order)
      : problem(404, 'entity_not_found', 'Pedido nao encontrado.')
  }),

  http.post(url('/api/v1/orders'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const body = (await request.json()) as {
      customer: { name: string; email: string }
      items: { product_id: string; quantity: number }[]
    }

    // Reserva de estoque, como o service faz: sem saldo, nada e criado.
    for (const item of body.items) {
      const balance = balanceOf(item.product_id)
      if (!balance) return problem(404, 'entity_not_found', 'Produto nao encontrado.')
      if (item.quantity > balance.quantity_available) {
        return problem(409, 'insufficient_stock', `Estoque insuficiente para ${balance.sku}.`, {
          sku: balance.sku,
          requested: item.quantity,
          available: balance.quantity_available,
        })
      }
    }

    const linhas = body.items.map((item) => {
      const product = products.find((candidate) => candidate.id === item.product_id)!
      const balance = balanceOf(item.product_id)!
      balance.quantity_reserved += item.quantity
      recompute(balance.product_id)
      return {
        product_id: product.id,
        sku: product.sku,
        description: product.name,
        quantity: item.quantity,
        unit_price_in_cents: product.price_in_cents,
        subtotal_in_cents: product.price_in_cents * item.quantity,
      }
    })

    const now = new Date().toISOString()
    const created: OrderDTO = {
      id: `ord_${Math.random().toString(36).slice(2, 10)}`,
      reference: `PED-${String(orders.length + 1).padStart(6, '0')}`,
      status: 'pending',
      customer: body.customer,
      items: linhas,
      total_in_cents: linhas.reduce((total, item) => total + item.subtotal_in_cents, 0),
      currency: 'BRL',
      cancellation_reason: null,
      placed_at: now,
      updated_at: now,
    }
    orders.unshift(created)
    return HttpResponse.json(created, { status: 201 })
  }),

  ...(['confirm', 'ship', 'deliver'] as const).map((acao) =>
    http.post(url(`/api/v1/orders/:orderId/${acao}`), async ({ request, params }) => {
      await delay(LATENCY_MS)
      if (!authorized(request)) return unauthorized()

      const order = orders.find((candidate) => candidate.id === params.orderId)
      if (!order) return problem(404, 'entity_not_found', 'Pedido nao encontrado.')

      const alvo: OrderStatusDTO =
        acao === 'confirm' ? 'confirmed' : acao === 'ship' ? 'shipped' : 'delivered'

      if (!TRANSICOES[order.status].includes(alvo)) {
        return problem(
          409,
          'invalid_status_transition',
          `Um pedido '${order.status}' nao pode ir para '${alvo}'.`,
          { current_status: order.status, target_status: alvo, allowed: TRANSICOES[order.status] },
        )
      }

      if (alvo === 'shipped') {
        // Envio baixa definitivamente o que estava reservado.
        for (const item of order.items) {
          const balance = balanceOf(item.product_id)
          if (balance) {
            balance.quantity_reserved -= item.quantity
            balance.quantity_on_hand -= item.quantity
            recompute(balance.product_id)
          }
        }
      }

      order.status = alvo
      order.updated_at = new Date().toISOString()
      return HttpResponse.json(order)
    }),
  ),

  http.post(url('/api/v1/orders/:orderId/cancel'), async ({ request, params }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const order = orders.find((candidate) => candidate.id === params.orderId)
    if (!order) return problem(404, 'entity_not_found', 'Pedido nao encontrado.')

    if (!TRANSICOES[order.status].includes('cancelled')) {
      return problem(
        409,
        'invalid_status_transition',
        `Um pedido '${order.status}' nao pode ser cancelado.`,
        { current_status: order.status, target_status: 'cancelled', allowed: TRANSICOES[order.status] },
      )
    }

    const body = (await request.json()) as { reason: string }
    for (const item of order.items) {
      const balance = balanceOf(item.product_id)
      if (balance) {
        balance.quantity_reserved -= item.quantity
        recompute(balance.product_id)
      }
    }

    order.status = 'cancelled'
    order.cancellation_reason = body.reason
    order.updated_at = new Date().toISOString()
    return HttpResponse.json(order)
  }),

  // -- painel ---------------------------------------------------------------
  http.get(url('/api/v1/dashboard'), async ({ request }) => {
    await delay(LATENCY_MS)
    if (!authorized(request)) return unauthorized()

    const faturaveis = orders.filter((order) => order.status !== 'cancelled')
    const receita = faturaveis.reduce((total, order) => total + order.total_in_cents, 0)
    const status: OrderStatusDTO[] = [
      'pending',
      'confirmed',
      'shipped',
      'delivered',
      'cancelled',
    ]

    // Mesma janela do backend, com zeros nos dias sem pedido: um grafico de
    // tempo com dias faltando sugere movimento onde nao houve.
    const DIAS = 14
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)
    const daily = Array.from({ length: DIAS }, (_, indice) => {
      const dia = new Date(hoje.getTime() - (DIAS - 1 - indice) * 86_400_000)
      const doDia = orders.filter((order) => {
        const criado = new Date(order.placed_at)
        criado.setHours(0, 0, 0, 0)
        return criado.getTime() === dia.getTime()
      })
      return {
        date: dia.toISOString().slice(0, 10),
        orders: doDia.length,
        revenue_in_cents: doDia
          .filter((order) => order.status !== 'cancelled')
          .reduce((total, order) => total + order.total_in_cents, 0),
      }
    })

    const baixos = stock
      .filter((balance) => balance.quantity_available <= 10)
      .sort((a, b) => a.quantity_available - b.quantity_available)
      .slice(0, 8)

    return HttpResponse.json({
      orders_total: orders.length,
      orders_open: orders.filter((order) =>
        ['pending', 'confirmed'].includes(order.status),
      ).length,
      orders_by_status: status.map((candidate) => ({
        status: candidate,
        count: orders.filter((order) => order.status === candidate).length,
      })),
      revenue_in_cents: receita,
      average_ticket_in_cents:
        faturaveis.length > 0 ? Math.floor(receita / faturaveis.length) : 0,
      products_total: products.length,
      products_active: products.filter((product) => product.active).length,
      units_on_hand: stock.reduce((total, balance) => total + balance.quantity_on_hand, 0),
      units_reserved: stock.reduce((total, balance) => total + balance.quantity_reserved, 0),
      out_of_stock: stock.filter((balance) => balance.quantity_available <= 0).length,
      low_stock: baixos.map((balance) => ({
        product_id: balance.product_id,
        sku: balance.sku,
        quantity_available: balance.quantity_available,
        quantity_reserved: balance.quantity_reserved,
      })),
      daily,
      recent_orders: orders.slice(0, 5).map((order) => ({
        id: order.id,
        reference: order.reference,
        status: order.status,
        customer_name: order.customer.name,
        item_count: order.items.reduce((total, item) => total + item.quantity, 0),
        total_in_cents: order.total_in_cents,
        placed_at: order.placed_at,
      })),
    })
  }),

  // -- saude ----------------------------------------------------------------
  http.get(url('/health/ready'), async () => {
    await delay(50)
    return HttpResponse.json({
      status: 'ready',
      dependencies: [{ name: 'postgres', healthy: true }],
    })
  }),

  // -- rede de seguranca ----------------------------------------------------
  // Precisa ser o ultimo: o MSW usa o primeiro handler que casa.
  //
  // Sem isto, uma rota sem mock vazaria para a rede, bateria no proxy do Vite
  // e voltaria como ECONNREFUSED - um erro que nao diz nada sobre a causa. Com
  // isto, o modo de demonstracao e fechado: ou ha um handler, ou a resposta
  // diz exatamente qual rota falta.
  http.all(url('/api/*'), ({ request }) => unhandled(request)),
  http.all(url('/health/*'), ({ request }) => unhandled(request)),
]
