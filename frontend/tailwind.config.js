/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
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
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07)',
      }
    },
  },
  plugins: [],
}
