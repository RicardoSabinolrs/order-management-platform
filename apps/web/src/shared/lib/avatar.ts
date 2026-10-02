/** Iniciais e cor estavel para avatares sem foto. */

const HUES = ['blue', 'pink', 'orange', 'teal', 'violet'] as const

export function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

/** Cor estavel por nome: a mesma pessoa sempre ganha o mesmo avatar. */
export function hueFor(name: string): (typeof HUES)[number] {
  let sum = 0
  for (const letter of name) sum = (sum + letter.charCodeAt(0)) % 997
  return HUES[sum % HUES.length]!
}
