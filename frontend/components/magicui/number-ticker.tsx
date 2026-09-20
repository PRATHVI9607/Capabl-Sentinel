'use client'

import { animate, useReducedMotion } from 'framer-motion'
import { useEffect, useRef } from 'react'

interface NumberTickerProps {
  value: number
  decimalPlaces?: number
  className?: string
}

export function NumberTicker({ value, decimalPlaces = 0, className }: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const reduce = useReducedMotion()

  useEffect(() => {
    if (!ref.current) return
    if (reduce) {
      ref.current.textContent = value.toFixed(decimalPlaces)
      return
    }
    const controls = animate(0, value, {
      duration: 0.8,
      ease: [0.4, 0, 0.2, 1],
      onUpdate: (latest) => {
        if (ref.current) ref.current.textContent = latest.toFixed(decimalPlaces)
      },
    })
    return () => controls.stop()
  }, [decimalPlaces, reduce, value])

  return <span ref={ref} className={className}>{value.toFixed(decimalPlaces)}</span>
}
