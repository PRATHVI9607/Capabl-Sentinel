'use client'

import { Bell, FileMagnifyingGlass, List, Pulse, ShieldCheck, SquaresFour, X } from '@phosphor-icons/react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

import { cn } from '@/lib/utils'

const items = [
  { href: '/analyze', label: 'Analyze', icon: Pulse },
  { href: '/dashboard', label: 'Dashboard', icon: SquaresFour },
  { href: '/incidents', label: 'Incidents', icon: FileMagnifyingGlass },
  { href: '/alerts', label: 'Alerts', icon: Bell },
] as const

function Mark() {
  return <span className="brand-mark" aria-hidden="true"><span /><span /><span /></span>
}

export function Navigation() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const links = items.map((item) => {
    const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
    const Icon = item.icon
    return (
      <Link key={item.href} href={item.href} aria-current={active ? 'page' : undefined} onClick={() => setOpen(false)} className={cn('nav-link group relative flex items-center gap-3 px-4 py-3 text-sm font-medium text-text-secondary', active && 'nav-link-active text-text-primary')}>
        <Icon aria-hidden="true" size={20} weight="light" className={cn('text-text-muted', active && 'text-accent')} />{item.label}
      </Link>
    )
  })

  return (
    <>
      <aside className="no-print hidden min-h-screen border-r border-border-subtle bg-[#080b10] md:flex md:flex-col">
        <Link href="/analyze" className="flex h-[88px] items-center gap-3 border-b border-border-subtle px-5 font-display text-sm font-bold tracking-[0.18em]"><Mark /> SENTINEL</Link>
        <nav className="mt-5 space-y-1 px-2" aria-label="Primary navigation">{links}</nav>
        <div className="mt-auto border-t border-border-subtle px-5 py-5"><div className="flex items-center gap-3 text-xs text-text-muted"><ShieldCheck aria-hidden="true" size={18} weight="light" /><span>Safety intelligence</span></div></div>
      </aside>
      <header className="no-print sticky top-0 z-50 flex h-16 items-center justify-between border-b border-border-subtle bg-bg-base/95 px-4 backdrop-blur md:hidden">
        <Link href="/analyze" className="flex items-center gap-3 font-display text-sm font-bold tracking-[0.16em]"><Mark /> SENTINEL</Link>
        <button type="button" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} className="grid h-10 w-10 place-items-center border border-border-default bg-bg-surface text-text-secondary" onClick={() => setOpen((value) => !value)}>{open ? <X size={20} weight="light" /> : <List size={20} weight="light" />}</button>
      </header>
      {open ? <nav className="no-print fixed inset-x-0 top-16 z-50 border-b border-border-default bg-bg-base p-3 md:hidden">{links}</nav> : null}
    </>
  )
}
