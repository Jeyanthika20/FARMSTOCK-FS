/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html','./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        lora: ['Lora', 'Georgia', 'serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      colors: {
        'farm-deep':   '#1a3d2b',
        'farm-mid':    '#2d6a4f',
        'farm-bright': '#40916c',
        'farm-light':  '#74c69d',
        'farm-pale':   '#d8f3dc',
        'farm-gold':   '#f4a261',
        'farm-cream':  '#f5f0e8',
        'farm-sky':    '#4cc9f0',
        'farm-red':    '#e76f51',
      }
    }
  },
  plugins: []
}
