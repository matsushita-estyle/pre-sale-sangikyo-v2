/**
 * Date utility functions
 */

import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

/**
 * Parse ISO date string from backend and convert to Date object
 * Backend returns ISO strings without timezone info (UTC assumed)
 *
 * @param dateStr ISO date string from backend (e.g., "2026-03-01T23:52:34.085081")
 * @returns Date object
 */
export function parseBackendDate(dateStr: string): Date {
  // タイムゾーン情報があるかチェック (Z または +HH:MM または -HH:MM)
  const hasTimezone = dateStr.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(dateStr)

  // タイムゾーン情報がない場合はUTCとして扱う
  return hasTimezone ? new Date(dateStr) : new Date(dateStr + 'Z')
}

/**
 * Format date as relative time (e.g., "3分前", "2時間前")
 *
 * @param dateStr ISO date string from backend
 * @returns Formatted relative time string
 */
export function formatRelativeTime(dateStr: string): string {
  try {
    const date = parseBackendDate(dateStr)
    return formatDistanceToNow(date, {
      addSuffix: true,
      locale: ja,
    })
  } catch (error) {
    console.error('Failed to format relative time:', error)
    return ''
  }
}
