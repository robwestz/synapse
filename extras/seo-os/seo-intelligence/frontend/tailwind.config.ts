import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brutalist color palette
        primary: '#FF0000',      // Aggressive red
        secondary: '#000000',    // Pure black
        background: '#FFFFFF',   // Clean white
        accent: '#00FF00',       // Hacker green
        warning: '#FF6600',      // Orange
        muted: '#CCCCCC',        // Light gray
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Inter Black', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'brutal-xl': ['4rem', { lineHeight: '1', fontWeight: '900' }],
        'brutal-lg': ['2.5rem', { lineHeight: '1.1', fontWeight: '900' }],
        'brutal-md': ['1.5rem', { lineHeight: '1.2', fontWeight: '700' }],
      },
      boxShadow: {
        'brutal': '8px 8px 0px 0px rgba(0, 0, 0, 1)',
        'brutal-sm': '4px 4px 0px 0px rgba(0, 0, 0, 1)',
        'brutal-lg': '12px 12px 0px 0px rgba(0, 0, 0, 1)',
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

export default config
