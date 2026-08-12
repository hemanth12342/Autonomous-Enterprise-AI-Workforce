/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        surface: {
          0:   '#0a0a0f',
          1:   '#0f0f1a',
          2:   '#13131f',
          3:   '#1a1a2e',
          4:   '#22223a',
          5:   '#2a2a4a',
        },
        accent: {
          purple: '#a855f7',
          cyan:   '#06b6d4',
          green:  '#10b981',
          amber:  '#f59e0b',
          red:    '#ef4444',
          pink:   '#ec4899',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      },
      animation: {
        'pulse-slow':     'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':        'fadeIn 0.5s ease-in-out',
        'slide-up':       'slideUp 0.3s ease-out',
        'glow':           'glow 2s ease-in-out infinite',
        'typing':         'typing 1s steps(40) infinite',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: 0 }, '100%': { transform: 'translateY(0)', opacity: 1 } },
        glow:    { '0%, 100%': { boxShadow: '0 0 5px rgba(99,102,241,0.5)' }, '50%': { boxShadow: '0 0 20px rgba(99,102,241,0.8)' } },
        typing:  { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
      },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
};
