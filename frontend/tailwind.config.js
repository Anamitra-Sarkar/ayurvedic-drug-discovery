/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Botanical palette: deep teal/emerald + warm amber/gold, cream background
        cream: {
          50: '#FDFBF5',
          100: '#FAF6EB',
          200: '#F3EBD3',
        },
        forest: {
          50: '#EFF8F3',
          100: '#D7EDDE',
          200: '#B0DBBE',
          300: '#7FC297',
          400: '#4DA672',
          500: '#2E8B57',
          600: '#0F5C4D',
          700: '#0C4A3E',
          800: '#0A3B32',
          900: '#072A24',
          950: '#041B17',
        },
        gold: {
          50: '#FDF8EC',
          100: '#FAEFD3',
          200: '#F4DFA5',
          300: '#EDC96F',
          400: '#E5B044',
          500: '#D9962B',
          600: '#B97A20',
          700: '#8F5D1D',
          800: '#6B451B',
        },
        clay: {
          100: '#F7E8E0',
          500: '#C96F4A',
          700: '#9C4E2E',
        },
        // keep legacy keys used by old components so nothing breaks
        ayur: {
          50: '#f6f7f0',
          100: '#e8e9d8',
          200: '#d1d3b0',
          300: '#b8b88a',
          400: '#9a9a6a',
          500: '#7a7a52',
          600: '#5f5f40',
          700: '#4a4a32',
          800: '#3a3a28',
          900: '#2a2a1e',
        },
        evidence: {
          db: '#0e7490',
          docking: '#7c3aed',
          ml: '#db2777',
          xai: '#ea580c',
          lit: '#15803d',
        }
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(7 42 36 / 0.06), 0 1px 2px -1px rgb(7 42 36 / 0.06)',
        'card-hover': '0 12px 28px -8px rgb(7 42 36 / 0.16), 0 4px 10px -4px rgb(7 42 36 / 0.08)',
        'lift': '0 18px 40px -12px rgb(7 42 36 / 0.25)',
        'glow': '0 0 0 3px rgb(217 150 43 / 0.25)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'pop-in': {
          '0%': { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
        'float-slow': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.45s ease both',
        'fade-in': 'fade-in 0.35s ease both',
        'pop-in': 'pop-in 0.28s cubic-bezier(0.16, 1, 0.3, 1) both',
        'float-slow': 'float-slow 7s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
