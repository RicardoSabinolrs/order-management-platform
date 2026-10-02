import { useState } from 'react'

import { hueFor, initials } from '@/shared/lib/avatar'

interface AvatarProps {
  name: string
  src?: string | null | undefined
  size?: number
  /** Anel em volta, para destacar o avatar sobre fundo colorido. */
  ring?: boolean
}

/**
 * Foto quando houver, iniciais quando nao. Decorativo: o nome sempre aparece
 * ao lado em texto, entao a imagem nao precisa ser lida.
 */
export function Avatar({ name, src, size = 36, ring = false }: AvatarProps) {
  // Foto quebrada (URL antiga, offline) cai nas iniciais em vez do icone de
  // imagem partida.
  const [failed, setFailed] = useState(false)
  const showPhoto = Boolean(src) && !failed

  return (
    <span
      className="avatar"
      data-hue={hueFor(name)}
      data-ring={ring || undefined}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
      aria-hidden="true"
    >
      {showPhoto ? (
        <img src={src ?? undefined} alt="" onError={() => setFailed(true)} />
      ) : (
        initials(name || '?')
      )}
    </span>
  )
}
