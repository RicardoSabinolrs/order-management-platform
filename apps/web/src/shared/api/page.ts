import type { PageDTO } from '@/shared/api/types'

export interface Page<ItemT> {
  items: ItemT[]
  total: number
  page: number
  pageSize: number
  pages: number
}

/** Converte a pagina da API, ja mapeando cada item para o tipo da interface. */
export function toPage<DtoT, ItemT>(dto: PageDTO<DtoT>, map: (item: DtoT) => ItemT): Page<ItemT> {
  return {
    items: dto.items.map(map),
    total: dto.total,
    page: dto.page,
    pageSize: dto.page_size,
    pages: Math.max(1, Math.ceil(dto.total / dto.page_size)),
  }
}
