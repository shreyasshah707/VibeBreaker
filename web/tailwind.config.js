/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        vibe: {
          bg: '#0d1117',
          surface: '#161b22',
          border: '#30363d',
          text: '#e6edf3',
          textMuted: '#8b949e',
          accent: '#58a6ff',
          accentHover: '#79b8ff',
          success: '#3fb950',
          warning: '#d29922',
          error: '#f85149',
          codeBg: '#010409',
        },
        dark: {
          bg: '#0d1117',
          card: '#161b22',
          foreground: '#e6edf3',
          muted: '#8b949e',
        },
        accent: '#58a6ff',
        card: '#161b22',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};