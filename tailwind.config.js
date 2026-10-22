/** @type {import('tailwindcss').config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#1a1a2e",
          card: "#16213e",
          foreground: "#f1f1f1",
          muted: "#6b7280",
        }
      }
    }
  }
}