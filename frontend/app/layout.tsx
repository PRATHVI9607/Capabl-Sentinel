import type { Metadata } from 'next'
import { Bricolage_Grotesque, DM_Sans, JetBrains_Mono } from 'next/font/google'
import { Toaster } from 'sonner'

import { AppShell } from '@/components/layout/AppShell'
import { QueryProvider } from '@/components/providers/QueryProvider'
import '@/styles/globals.css'

const display = Bricolage_Grotesque({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const body = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
})

const mono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'SENTINEL Safety Intelligence',
    template: '%s | SENTINEL',
  },
  description:
    'Explainable workplace incident analysis with precursor evidence and regulatory traceability.',
  icons: { icon: '/icon.svg' },
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable} dark`}>
      <body>
        <QueryProvider>
          <AppShell>{children}</AppShell>
          <Toaster
            position="bottom-right"
            theme="dark"
            toastOptions={{
              classNames: {
                toast: 'border-border-default bg-bg-card text-text-primary',
                description: 'text-text-secondary',
              },
            }}
          />
        </QueryProvider>
      </body>
    </html>
  )
}
