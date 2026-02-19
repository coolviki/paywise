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
        primary: {
          50: '#e6f2ff',
          100: '#b3d9ff',
          200: '#80bfff',
          300: '#4da6ff',
          400: '#1a8cff',
          500: '#0071E3',
          600: '#005bb5',
          700: '#004488',
          800: '#002e5a',
          900: '#00172d',
        },
        accent: {
          50: '#e8f9ed',
          100: '#b9edc8',
          200: '#8ae1a3',
          300: '#5bd57e',
          400: '#34C759',
          500: '#2aa147',
          600: '#207b36',
          700: '#165524',
          800: '#0c2f13',
          900: '#020902',
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
