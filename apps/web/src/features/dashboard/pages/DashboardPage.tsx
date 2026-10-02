import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchOverview } from '@/features/dashboard/api/dashboard'
import { KpiTile } from '@/features/dashboard/components/KpiTile'
import type { DailyPoint } from '@/features/dashboard/types'
import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import type { OrderStatus } from '@/features/orders/types'
import { DonutChart } from '@/shared/charts/DonutChart'
import { Gauge } from '@/shared/charts/Gauge'
import { TrendChart } from '@/shared/charts/TrendChart'
import { useI18n } from '@/shared/i18n/useI18n'
import { Avatar } from '@/shared/ui/Avatar'
import { Card } from '@/shared/ui/Card'
import {
  IconAlert,
  IconArrowRight,
  IconChevronRight,
  IconDollar,
  IconLock,
  IconOrders,
  IconProducts,
  IconTag,
} from '@/shared/ui/icons'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

type Medida = 'orders' | 'revenue'

// As mesmas cores dos selos de status: a fatia da rosca e o selo da tabela
// falam a mesma lingua.
const STATUS_COLORS: Record<OrderStatus, string> = {
  pending: 'var(--warning)',
  confirmed: 'var(--info)',
  shipped: 'var(--serious)',
  delivered: 'var(--good)',
  cancelled: 'var(--critical)',
}

function percentual(parte: number, todo: number): number {
  return todo > 0 ? Math.round((parte / todo) * 100) : 0
}

export function DashboardPage() {
  const [medida, setMedida] = useState<Medida>('orders')
  const { t, format } = useI18n()

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchOverview,
    // Tela de acompanhamento: vale manter perto do tempo real.
    refetchInterval: 30_000,
  })

  if (isPending) {
    return (
      <div className="stack">
        <div className="kpis">
          {Array.from({ length: 5 }, (_, index) => (
            <div key={index} className="kpi">
              <SkeletonRows rows={2} />
            </div>
          ))}
        </div>
        <Card title={t.common.loading}>
          <SkeletonRows rows={6} />
        </Card>
      </div>
    )
  }

  if (isError) {
    return (
      <StateMessage
        kind="error"
        title={t.dashboard.loadError}
        description={error.message}
      />
    )
  }

  const serie = data.daily.map((ponto) => ({
    date: ponto.date,
    value: medida === 'orders' ? ponto.orders : ponto.revenueInCents,
  }))

  const totalPeriodo = serie.reduce((soma, ponto) => soma + ponto.value, 0)

  // Ultimos 7 dias contra os 7 anteriores, da mesma serie que ja veio na
  // resposta - sem uma segunda consulta so para exibir a variacao.
  const metade = Math.floor(data.daily.length / 2)
  const variacao = (selecionar: (ponto: DailyPoint) => number) => {
    const somar = (pontos: DailyPoint[]) => pontos.reduce((t, p) => t + selecionar(p), 0)
    const anterior = somar(data.daily.slice(0, metade))
    const atual = somar(data.daily.slice(metade))
    if (anterior === 0) return undefined
    return {
      percent: Math.round(((atual - anterior) / anterior) * 100),
      label: t.dashboard.last7Days,
    }
  }

  const contagem = (status: OrderStatus) =>
    data.ordersByStatus.find((entrada) => entrada.status === status)?.count ?? 0
  const pedidosNaFila = data.ordersByStatus.reduce((soma, entrada) => soma + entrada.count, 0)
  const cancelados = contagem('cancelled')
  const entregues = contagem('delivered')
  // Cancelado nao conta na base: um pedido cancelado nunca vai ser entregue,
  // e deixa-lo ali faria a taxa cair por um motivo que nao e de expedicao.
  const validos = pedidosNaFila - cancelados
  const emAndamento = validos - entregues

  const disponivel = data.unitsOnHand - data.unitsReserved
  const comSaldo = data.productsTotal - data.outOfStock

  return (
    <div className="dash">
      <section className="hero-card">
        <div className="hero-card__body">
          <p className="hero-card__eyebrow">{t.dashboard.heroEyebrow}</p>
          <h1 className="hero-card__title">{t.pages.dashboard.subtitle}</h1>
          <p className="hero-card__text">{t.dashboard.heroSummary(data.ordersOpen, data.outOfStock)}</p>
          <div className="hero-card__actions">
            <Link className="btn btn--light" to="/pedidos">
              {t.dashboard.heroOrders}
              <IconArrowRight size={15} />
            </Link>
            <Link className="btn btn--glass" to="/estoque">
              {t.dashboard.heroStock}
            </Link>
          </div>
        </div>
        <div className="hero-card__art" aria-hidden="true">
          <div className="hero-card__glass hero-card__glass--a">
            <span>{t.dashboard.revenue}</span>
            <strong>{format.compactCurrency(data.revenueInCents)}</strong>
          </div>
          <div className="hero-card__glass hero-card__glass--b">
            <span>{t.dashboard.averageTicket}</span>
            <strong>{format.currency(data.averageTicketInCents)}</strong>
          </div>
          <svg className="hero-card__rings" viewBox="0 0 200 200">
            <circle cx="100" cy="100" r="92" />
            <circle cx="100" cy="100" r="64" />
            <circle cx="100" cy="100" r="36" />
          </svg>
        </div>
      </section>

      <section className="kpis" aria-label={t.dashboard.kpiRegion}>
        <KpiTile
          icon={<IconOrders size={18} />}
          hue="blue"
          label={t.dashboard.openOrders}
          value={data.ordersOpen}
          delta={variacao((ponto) => ponto.orders)}
          hint={t.dashboard.ordersInDays(data.ordersTotal, data.daily.length)}
          trend={data.daily.map((ponto) => ponto.orders)}
        />
        <KpiTile
          icon={<IconDollar size={18} />}
          hue="pink"
          label={t.dashboard.revenue}
          value={format.currency(data.revenueInCents)}
          delta={variacao((ponto) => ponto.revenueInCents)}
          hint={t.dashboard.notCancelled}
          trend={data.daily.map((ponto) => ponto.revenueInCents)}
        />
        <KpiTile
          icon={<IconTag size={18} />}
          hue="orange"
          label={t.dashboard.averageTicket}
          value={format.currency(data.averageTicketInCents)}
          hint={t.dashboard.perOrder}
        />
        <KpiTile
          icon={<IconLock size={18} />}
          hue="teal"
          label={t.dashboard.reservedUnits}
          value={data.unitsReserved}
          hint={t.dashboard.unitsOnHand(data.unitsOnHand)}
          tone={data.unitsReserved > 0 ? 'warn' : 'neutral'}
        />
        <KpiTile
          icon={<IconAlert size={18} />}
          hue="violet"
          label={t.dashboard.outOfStock}
          value={data.outOfStock}
          hint={t.dashboard.activeOfTotal(data.productsActive, data.productsTotal)}
          tone={data.outOfStock > 0 ? 'critical' : 'neutral'}
        />
      </section>

      <div className="dash__row dash__row--wide">
        <Card
          title={medida === 'orders' ? t.dashboard.ordersPerDay : t.dashboard.revenuePerDay}
          description={
            medida === 'orders'
              ? t.dashboard.ordersInPeriod(totalPeriodo, serie.length)
              : t.dashboard.revenueInPeriod(format.currency(totalPeriodo), serie.length)
          }
          actions={
            <div className="chips" role="group" aria-label={t.dashboard.measure}>
              <button
                type="button"
                className="chip"
                aria-pressed={medida === 'orders'}
                onClick={() => setMedida('orders')}
              >
                {t.dashboard.measureOrders}
              </button>
              <button
                type="button"
                className="chip"
                aria-pressed={medida === 'revenue'}
                onClick={() => setMedida('revenue')}
              >
                {t.dashboard.measureRevenue}
              </button>
            </div>
          }
        >
          <TrendChart
            points={serie}
            label={medida === 'orders' ? t.dashboard.seriesOrders : t.dashboard.seriesRevenue}
            description={t.dashboard.chartLabel(
              medida === 'orders' ? t.dashboard.seriesOrders : t.dashboard.seriesRevenue,
              serie.length,
            )}
            format={
              medida === 'orders' ? (valor) => format.number(Math.round(valor)) : format.compactCurrency
            }
          />
        </Card>

        <Card title={t.dashboard.byStatus} description={t.dashboard.byStatusHint}>
          <DonutChart
            unit={t.dashboard.ordersUnit}
            ariaLabel={t.dashboard.distribution}
            data={data.ordersByStatus.map((entrada) => ({
              key: entrada.status,
              label: t.status[entrada.status],
              value: entrada.count,
              color: STATUS_COLORS[entrada.status],
            }))}
          />
        </Card>
      </div>

      <div className="dash__row dash__row--thirds">
        <Card
          title={t.dashboard.reorder}
          description={t.dashboard.reorderHint}
          actions={
            <Link className="btn btn--secondary btn--sm" to="/estoque">
              {t.dashboard.heroStock}
              <IconChevronRight size={14} />
            </Link>
          }
        >
          {data.lowStock.length === 0 ? (
            <StateMessage
              kind="empty"
              title={t.dashboard.reorderEmpty}
              description={t.dashboard.reorderEmptyHint}
            />
          ) : (
            <ul className="reorder">
              {data.lowStock.map((item) => (
                <li key={item.productId} className="reorder__row">
                  <span className="reorder__icon" data-zero={item.quantityAvailable === 0} aria-hidden="true">
                    <IconProducts size={16} />
                  </span>
                  <span className="reorder__sku">
                    {item.sku}
                    <span className="reorder__meta">
                      {item.quantityReserved > 0
                        ? t.dashboard.reservedInOrders(item.quantityReserved)
                        : t.dashboard.noReservation}
                    </span>
                  </span>
                  <span className="reorder__value">
                    <span className="reorder__count" data-zero={item.quantityAvailable === 0}>
                      {item.quantityAvailable}
                    </span>
                    <span className="reorder__unit">{t.dashboard.available}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title={t.dashboard.deliveryRate} description={t.dashboard.deliveryRateHint}>
          <Gauge percent={percentual(entregues, validos)} label={t.dashboard.delivered} />
          <dl className="gauge-stats">
            <div>
              <dt>{t.dashboard.statDelivered}</dt>
              <dd>{entregues}</dd>
            </div>
            <div>
              <dt>{t.dashboard.statInProgress}</dt>
              <dd>{emAndamento}</dd>
            </div>
            <div>
              <dt>{t.dashboard.statCancelled}</dt>
              <dd>{percentual(cancelados, pedidosNaFila)}%</dd>
            </div>
          </dl>
        </Card>

        <Card title={t.dashboard.stockHealth} description={t.dashboard.stockHealthHint}>
          <ul className="meters">
            <li className="meter">
              <div className="meter__head">
                <span className="meter__label">{t.dashboard.availableUnits}</span>
                <span className="meter__value">
                  {disponivel} <span>{t.dashboard.ofTotal(data.unitsOnHand)}</span>
                </span>
              </div>
              <span className="meter__track" aria-hidden="true">
                <span
                  className="meter__fill"
                  data-hue="teal"
                  style={{ width: `${percentual(disponivel, data.unitsOnHand)}%` }}
                />
              </span>
            </li>
            <li className="meter">
              <div className="meter__head">
                <span className="meter__label">{t.dashboard.productsWithBalance}</span>
                <span className="meter__value">
                  {comSaldo} <span>{t.dashboard.ofTotal(data.productsTotal)}</span>
                </span>
              </div>
              <span className="meter__track" aria-hidden="true">
                <span
                  className="meter__fill"
                  data-hue="blue"
                  style={{ width: `${percentual(comSaldo, data.productsTotal)}%` }}
                />
              </span>
            </li>
            <li className="meter">
              <div className="meter__head">
                <span className="meter__label">{t.dashboard.activeProducts}</span>
                <span className="meter__value">
                  {data.productsActive} <span>{t.dashboard.ofTotal(data.productsTotal)}</span>
                </span>
              </div>
              <span className="meter__track" aria-hidden="true">
                <span
                  className="meter__fill"
                  data-hue="violet"
                  style={{ width: `${percentual(data.productsActive, data.productsTotal)}%` }}
                />
              </span>
            </li>
          </ul>
        </Card>
      </div>

      <Card
        title={t.dashboard.recentOrders}
        padding="flush"
        actions={
          <Link className="btn btn--secondary btn--sm" to="/pedidos">
            {t.dashboard.seeAll}
            <IconChevronRight size={14} />
          </Link>
        }
      >
        {data.recentOrders.length === 0 ? (
          <StateMessage
            kind="empty"
            title={t.dashboard.recentEmpty}
            description={t.dashboard.recentEmptyHint}
          />
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <caption className="visually-hidden">{t.dashboard.recentOrdersCaption}</caption>
              <thead>
                <tr>
                  <th scope="col">{t.dashboard.colCustomer}</th>
                  <th scope="col">{t.dashboard.colReference}</th>
                  <th scope="col" className="table__number">
                    {t.dashboard.colItems}
                  </th>
                  <th scope="col">{t.dashboard.colStatus}</th>
                  <th scope="col" className="table__number">
                    {t.dashboard.colTotal}
                  </th>
                  <th scope="col">{t.dashboard.colCreatedAt}</th>
                </tr>
              </thead>
              <tbody>
                {data.recentOrders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <span className="person">
                        <Avatar name={order.customerName} size={34} />
                        <span className="table__primary">{order.customerName}</span>
                      </span>
                    </td>
                    <td>
                      <Link className="table__link" to={`/pedidos/${order.id}`}>
                        {order.reference}
                      </Link>
                    </td>
                    <td className="table__number">{order.itemCount}</td>
                    <td>
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="table__number">{format.currency(order.totalInCents)}</td>
                    <td>{format.dateTime(order.placedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
