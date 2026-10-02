/**
 * Espera com a forma do conteudo que vai chegar.
 *
 * Um "Carregando..." centralizado faz a pagina saltar quando os dados chegam;
 * o esqueleto ja ocupa o espaco final.
 */
export function Skeleton({ height = 14, width = '100%' }: { height?: number; width?: string }) {
  return <span className="skeleton" style={{ height, width, display: 'block' }} />
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="skeleton-rows" role="status" aria-label="Carregando">
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} width={index === 0 ? '40%' : '100%'} />
      ))}
    </div>
  )
}
