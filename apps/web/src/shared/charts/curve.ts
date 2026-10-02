/**
 * Curva suave por interpolacao cubica monotona (Fritsch-Carlson).
 *
 * Uma spline comum "passa do ponto" entre dois valores e desenharia um vale
 * abaixo de zero num dia sem pedidos. A monotona so curva onde o dado curva:
 * nunca inventa pico nem vale que a serie nao tem.
 */
export type Ponto = readonly [x: number, y: number]

export function caminhoSuave(pontos: readonly Ponto[]): string {
  const total = pontos.length
  if (total === 0) return ''
  const [x0, y0] = pontos[0]!
  if (total === 1) return `M ${x0},${y0}`

  const inclinacoes: number[] = []
  for (let i = 0; i < total - 1; i++) {
    const [xa, ya] = pontos[i]!
    const [xb, yb] = pontos[i + 1]!
    inclinacoes.push((yb - ya) / (xb - xa || 1))
  }

  const tangentes = pontos.map((_, i) => {
    if (i === 0) return inclinacoes[0]!
    if (i === total - 1) return inclinacoes[total - 2]!
    const antes = inclinacoes[i - 1]!
    const depois = inclinacoes[i]!
    return antes * depois <= 0 ? 0 : (antes + depois) / 2
  })

  for (let i = 0; i < total - 1; i++) {
    const m = inclinacoes[i]!
    if (m === 0) {
      tangentes[i] = 0
      tangentes[i + 1] = 0
      continue
    }
    const a = tangentes[i]! / m
    const b = tangentes[i + 1]! / m
    const soma = a * a + b * b
    if (soma > 9) {
      const fator = 3 / Math.sqrt(soma)
      tangentes[i] = fator * a * m
      tangentes[i + 1] = fator * b * m
    }
  }

  let caminho = `M ${x0},${y0}`
  for (let i = 0; i < total - 1; i++) {
    const [xa, ya] = pontos[i]!
    const [xb, yb] = pontos[i + 1]!
    const terco = (xb - xa) / 3
    caminho +=
      ` C ${xa + terco},${ya + tangentes[i]! * terco}` +
      ` ${xb - terco},${yb - tangentes[i + 1]! * terco}` +
      ` ${xb},${yb}`
  }
  return caminho
}
