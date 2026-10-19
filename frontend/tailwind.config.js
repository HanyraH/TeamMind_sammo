/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#070C18',
          900: '#0B1120',
          850: '#0F172A', // ТЗ: кастомная тёмная тема #0F172A
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
        },
        brand: {
          blue: '#3B82F6',
          sky: '#38BDF8',
          indigo: '#6366F1',
          teal: '#14B8A6',
          violet: '#8B5CF6'
        }
      }
    },
  },
  plugins: [],
}
