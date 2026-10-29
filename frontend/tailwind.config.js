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
        // Light Theme: Warm Editorial / Creative Studio
        loomi: {
          ivory: '#F7F2E9',      // Warm ivory background
          coral: '#E66A4E',      // Brand coral orange
          'coral-hover': '#D45A3F',
          'coral-light': '#FCEEEA',
          ink: '#252821',        // Ink charcoal text & primary
          sand: '#EFE5D8',       // Sand beige surface / borders
          'sand-dark': '#E2D4C3',
          secondary: '#77746D',  // Editorial secondary text
          border: '#E8DED1',     // Soft border

          // Dark Theme: Carefully designed dark editorial palette
          'dark-bg': '#141613',       // Deep editorial ink
          'dark-surface': '#1C1F1A',  // Card and drawer surface
          'dark-elevated': '#252822', // Hover & elevated items
          'dark-border': '#2E322A',   // Subtle borders
          'dark-text': '#F5EFE6',     // High contrast soft white
          'dark-muted': '#9E9A91',    // Secondary muted text
          'dark-coral': '#F07A60',    // Glowing coral accent
        },
      },
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'serif'],
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'warm': '0 4px 20px -2px rgba(37, 40, 33, 0.05), 0 2px 6px -1px rgba(37, 40, 33, 0.03)',
        'warm-lg': '0 10px 30px -4px rgba(37, 40, 33, 0.08), 0 4px 12px -2px rgba(37, 40, 33, 0.04)',
        'coral-glow': '0 0 25px -5px rgba(230, 106, 78, 0.3)',
      },
    },
  },
  plugins: [],
};
