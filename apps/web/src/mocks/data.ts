/**
 * Dados de demonstracao, no mesmo formato que a API devolve.
 *
 * Servem para trabalhar no frontend sem backend no ar (`make dev-frontend`).
 * Com a API real, o MSW fica desligado e nada aqui e carregado - nenhum
 * componente importa deste modulo.
 */

import { DEMO_CREDENTIALS } from '@/features/auth/demo'
import type { OrderDTO, OrderStatusDTO, ProductDTO, StockDTO, UserDTO } from '@/shared/api/types'

export { DEMO_CREDENTIALS }

// O operador padrao e o administrador raiz, como no backend: e ele quem
// cadastra o restante da equipe.
export const DEMO_USER: UserDTO = {
  id: 'usr_operator',
  name: 'Operador',
  email: DEMO_CREDENTIALS.email,
  role: 'admin',
  avatar_url: '/avatars/operador.jpg',
}

/** Usuario do mock com a senha em claro - so existe aqui, nunca na API. */
export type MockUser = UserDTO & { password: string }

function buildUsers(): MockUser[] {
  return [
    { ...DEMO_USER, password: DEMO_CREDENTIALS.password },
    {
      id: 'usr_0002',
      name: 'Marina Duarte',
      email: 'marina.duarte@sabinolabs.dev',
      role: 'operator',
      avatar_url: null,
      password: 'marina1234',
    },
    {
      id: 'usr_0003',
      name: 'Joao Pires',
      email: 'joao.pires@sabinolabs.dev',
      role: 'viewer',
      avatar_url: null,
      password: 'joao12345',
    },
  ]
}

export const users: MockUser[] = buildUsers()

const CATALOGO: [string, string, string, number, number][] = [
  ['CAF-500', 'Cafe torrado e moido 500g', 'Blend da casa, torra media', 3290, 120],
  ['CHA-VER-100', 'Cha verde folhas 100g', 'Colheita de primavera', 2150, 80],
  ['CAN-ARO-01', 'Caneca ceramica 350ml', 'Esmaltada, apta a lava-loucas', 4900, 45],
  ['FIL-PAP-103', 'Filtro de papel n.103 (100un)', 'Coador grande', 1290, 200],
  ['PRE-FRA-600', 'Prensa francesa 600ml', 'Vidro borossilicato e aco inox', 18990, 18],
  ['MOE-MAN-01', 'Moedor manual em aco', 'Moagem regulavel', 24500, 12],
  ['ACU-MAS-500', 'Acucar mascavo organico 500g', 'Certificado organico', 1890, 60],
]

const CLIENTES = [
  { name: 'Marina Duarte', email: 'marina.duarte@exemplo.com' },
  { name: 'Rafael Nogueira', email: 'rafael.nogueira@exemplo.com' },
  { name: 'Comercial Andrade ME', email: 'compras@andrade.com.br' },
  { name: 'Beatriz Lemos', email: 'beatriz.lemos@exemplo.com' },
  { name: 'Distribuidora Vale Verde', email: 'pedidos@valeverde.com.br' },
]

const STATUS_CICLO: OrderStatusDTO[] = [
  'delivered',
  'shipped',
  'confirmed',
  'pending',
  'cancelled',
  'pending',
  'confirmed',
]

const AGORA = Date.parse('2026-09-30T12:00:00Z')

function buildProducts(): ProductDTO[] {
  return CATALOGO.map(([sku, name, description, price], index) => ({
    id: `prd_${String(index + 1).padStart(4, '0')}`,
    sku,
    name,
    description,
    price_in_cents: price,
    currency: 'BRL',
    active: true,
    created_at: new Date(AGORA - index * 86_400_000).toISOString(),
    updated_at: new Date(AGORA - index * 86_400_000).toISOString(),
  }))
}

function buildStock(catalogo: ProductDTO[]): StockDTO[] {
  return CATALOGO.map(([sku, , , , quantidade], index) => ({
    product_id: catalogo[index]!.id,
    sku,
    quantity_on_hand: quantidade,
    quantity_reserved: 0,
    quantity_available: quantidade,
    updated_at: new Date(AGORA).toISOString(),
  }))
}

export const products: ProductDTO[] = buildProducts()
export const stock: StockDTO[] = buildStock(products)

function buildOrder(index: number): OrderDTO {
  const customer = CLIENTES[index % CLIENTES.length]!
  const primeiro = products[index % products.length]!
  const segundo = products[(index + 3) % products.length]!

  const itens = [
    { produto: primeiro, quantidade: 1 + (index % 4) },
    { produto: segundo, quantidade: 1 + (index % 2) },
  ]
  const total = itens.reduce(
    (soma, item) => soma + item.produto.price_in_cents * item.quantidade,
    0,
  )
  const placedAt = new Date(AGORA - index * 5.5 * 3_600_000)
  const status = STATUS_CICLO[index % STATUS_CICLO.length]!

  return {
    id: `ord_${String(index + 1).padStart(4, '0')}`,
    reference: `PED-${String(index + 1).padStart(6, '0')}`,
    status,
    customer,
    items: itens.map((item) => ({
      product_id: item.produto.id,
      sku: item.produto.sku,
      description: item.produto.name,
      quantity: item.quantidade,
      unit_price_in_cents: item.produto.price_in_cents,
      subtotal_in_cents: item.produto.price_in_cents * item.quantidade,
    })),
    total_in_cents: total,
    currency: 'BRL',
    cancellation_reason: status === 'cancelled' ? 'Cliente desistiu da compra' : null,
    placed_at: placedAt.toISOString(),
    updated_at: new Date(placedAt.getTime() + 5_400_000).toISOString(),
  }
}

export const orders: OrderDTO[] = Array.from({ length: 23 }, (_, index) => buildOrder(index))

/**
 * Reconstroi o estado inicial entre os testes.
 *
 * Os arrays sao substituidos por inteiro, nao ajustados item a item: um teste
 * que cadastra produto deixa a lista maior que o catalogo original.
 */
export function resetDemoData(): void {
  const catalogo = buildProducts()
  products.splice(0, products.length, ...catalogo)
  stock.splice(0, stock.length, ...buildStock(catalogo))
  orders.splice(0, orders.length, ...Array.from({ length: 23 }, (_, i) => buildOrder(i)))
  users.splice(0, users.length, ...buildUsers())
}
