import type { Config } from 'tailwindcss'

const withOpacity = (variable: string) =>
  `rgb(from var(${variable}) r g b / <alpha-value>)`

const config: Config = {
  darkMode: ['class'],
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './hooks/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-base': withOpacity('--bg-base'),
        'bg-surface': withOpacity('--bg-surface'),
        'bg-card': withOpacity('--bg-card'),
        'bg-card-hover': withOpacity('--bg-card-hover'),
        'border-subtle': withOpacity('--border-subtle'),
        'border-default': withOpacity('--border-default'),
        'border-strong': withOpacity('--border-strong'),
        'severity-critical': withOpacity('--severity-critical'),
        'severity-high': withOpacity('--severity-high'),
        'severity-medium': withOpacity('--severity-medium'),
        'severity-low': withOpacity('--severity-low'),
        accent: withOpacity('--accent'),
        'accent-hover': withOpacity('--accent-hover'),
        'text-primary': withOpacity('--text-primary'),
        'text-secondary': withOpacity('--text-secondary'),
        'text-muted': withOpacity('--text-muted'),
        'stage-idle': withOpacity('--stage-idle'),
        'stage-active': withOpacity('--stage-active'),
        'stage-complete': withOpacity('--stage-complete'),
        'stage-error': withOpacity('--stage-error'),
      },
      fontFamily: {
        display: ['var(--font-display)'],
        body: ['var(--font-body)'],
        mono: ['var(--font-mono)'],
      },
      boxShadow: {
        card: '0 18px 60px rgba(2, 4, 18, 0.24)',
        accent: '0 0 0 1px rgba(79, 142, 247, 0.16), 0 16px 50px rgba(79, 142, 247, 0.08)',
      },
      keyframes: {
        beam: {
          '0%': { transform: 'translate3d(-12%, 0, 0)', opacity: '0' },
          '18%': { opacity: '0.42' },
          '82%': { opacity: '0.42' },
          '100%': { transform: 'translate3d(12%, 0, 0)', opacity: '0' },
        },
        'border-orbit': {
          to: { transform: 'rotate(360deg)' },
        },
        meteor: {
          '0%': { transform: 'translate3d(0, 0, 0)', opacity: '0' },
          '12%': { opacity: '0.38' },
          '70%': { opacity: '0.18' },
          '100%': { transform: 'translate3d(-360px, 360px, 0)', opacity: '0' },
        },
        shine: {
          '0%': { backgroundPosition: '160% 0' },
          '100%': { backgroundPosition: '-60% 0' },
        },
      },
      animation: {
        beam: 'beam 10s ease-in-out infinite',
        'border-orbit': 'border-orbit 8s linear infinite',
        meteor: 'meteor 12s linear infinite',
        shine: 'shine 1.4s ease-in-out 1',
      },
    },
  },
  plugins: [],
}

export default config
