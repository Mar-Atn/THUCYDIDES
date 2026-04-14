/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Light theme: "Strategic Paper"
        base: '#F5F6F8',
        card: '#FFFFFF',
        border: '#D8DCE5',
        'text-primary': '#1A2332',
        'text-secondary': '#4A5568',
        action: '#1A5276',
        accent: '#C4922A',
        success: '#2E7D4F',
        warning: '#B8762E',
        danger: '#B03A3A',
        // Dark theme tokens (used via dark: prefix)
        'dark-base': '#0D1B2A',
        'dark-card': '#1B2A3E',
        'dark-border': '#253D54',
        'dark-text-primary': '#D4DEE8',
        'dark-text-secondary': '#7A8FA3',
        'dark-action': '#5B9BD5',
        'dark-accent': '#E8B84D',
      },
      fontFamily: {
        heading: ['"Playfair Display"', 'Georgia', 'serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
        data: ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        'display': ['2.5rem', { lineHeight: '1.2', fontWeight: '700' }],
        'h1': ['1.75rem', { lineHeight: '1.3', fontWeight: '700' }],
        'h2': ['1.375rem', { lineHeight: '1.4', fontWeight: '600' }],
        'h3': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
        'body': ['1rem', { lineHeight: '1.6', fontWeight: '400' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
        'caption': ['0.75rem', { lineHeight: '1.4', fontWeight: '500' }],
        'data': ['1rem', { lineHeight: '1.4', fontWeight: '500' }],
        'data-lg': ['1.5rem', { lineHeight: '1.3', fontWeight: '700' }],
      },
    },
  },
  plugins: [],
}
