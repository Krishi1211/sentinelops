/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B1220',
        panel: '#121B2E',
        textPrimary: '#E4E9F2',
        textSecondary: '#6B7A99',
        detector: '#4FC3E0',
        diagnostician: '#E0A64F',
        remediator: '#5FD68A',
        alert: '#E0574F',
      },
      fontFamily: {
        sans: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
