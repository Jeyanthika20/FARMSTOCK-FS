/**
 * useWebSocket.js — Real-time WebSocket hook
 * Connects to /ws/prices or /ws/alerts, auto-reconnects on disconnect.
 */
import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket(path) {
  const [messages, setMessages] = useState([])
  const [lastMessage, setLastMessage] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const retryRef = useRef(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.hostname
    const port = window.location.port === '5173' ? '8000' : window.location.port
    const url = `${protocol}://${host}:${port}${path}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log(` WebSocket connected: ${path}`)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          setMessages(prev => [data, ...prev].slice(0, 50))
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        // Auto-reconnect after 3s
        retryRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        setConnected(false)
        ws.close()
      }
    } catch (e) {
      console.error('WS connection error:', e)
      retryRef.current = setTimeout(connect, 5000)
    }
  }, [path])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { messages, lastMessage, connected }
}
