'use client'

import { useEffect, useState } from 'react'

import type { StreamStatus, StreamUpdate } from '@/lib/types'

interface SSEState {
  updates: StreamUpdate[]
  lastUpdate: StreamUpdate | null
  error: string | null
  isConnected: boolean
}

const statuses: StreamStatus[] = ['started', 'completed', 'error', 'alive']

function isStreamUpdate(value: unknown): value is StreamUpdate {
  if (typeof value !== 'object' || value === null) return false
  const record = value as Record<string, unknown>
  return (
    typeof record.stage === 'string' &&
    typeof record.status === 'string' &&
    statuses.includes(record.status as StreamStatus) &&
    typeof record.message === 'string' &&
    (record.data === null || typeof record.data === 'object') &&
    typeof record.timestamp === 'string'
  )
}

export function useSSE(url: string | null): SSEState {
  const [updates, setUpdates] = useState<StreamUpdate[]>([])
  const [lastUpdate, setLastUpdate] = useState<StreamUpdate | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    setUpdates([])
    setLastUpdate(null)
    setError(null)
    setIsConnected(false)
    if (!url) return

    const source = new EventSource(url)

    source.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    source.onmessage = (event) => {
      try {
        const parsed: unknown = JSON.parse(event.data)
        if (!isStreamUpdate(parsed)) throw new Error('Unexpected stream payload.')
        if (parsed.stage === 'heartbeat') return

        setUpdates((current) => [...current, parsed])
        setLastUpdate(parsed)

        if (parsed.stage === 'complete' || parsed.stage === 'error') {
          setIsConnected(false)
          source.close()
        }
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : 'The stream sent unreadable data.')
      }
    }

    source.onerror = () => {
      setIsConnected(false)
      setError('The analysis stream disconnected.')
    }

    return () => source.close()
  }, [url])

  return { updates, lastUpdate, error, isConnected }
}
