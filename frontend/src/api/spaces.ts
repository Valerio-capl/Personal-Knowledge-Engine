import { apiGet } from './client'
import type { SpaceResponse } from '../types/api'

export function getSpaces(): Promise<SpaceResponse[]> {
  return apiGet<SpaceResponse[]>('/spaces')
}