'use client'

import { motion, useReducedMotion } from 'framer-motion'

interface TextGenerateEffectProps {
  text: string
  className?: string
}

export function TextGenerateEffect({ text, className }: TextGenerateEffectProps) {
  const reduce = useReducedMotion()
  return (
    <motion.h1
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      className={className}
    >
      {text}
    </motion.h1>
  )
}
