/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0b0f19",
        card: {
          DEFAULT: "#111827",
          subtle: "#162032",
          hover: "#1a273e",
        },
        border: {
          DEFAULT: "#1f293d",
          muted: "#172033",
          bright: "#2d3e58",
        },
        accent: {
          cyan: "#06b6d4",
          "cyan-light": "#22d3ee",
          blue: "#3b82f6",
          "blue-light": "#60a5fa",
          violet: "#8b5cf6",
          "violet-light": "#a78bfa",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "Inter",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};