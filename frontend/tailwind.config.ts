import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#050a0f",
          secondary: "#080e15",
          card: "#0a1520",
          card2: "#0c1a28",
          header: "#0d2235",
        },
        icu: {
          green: "#00ff88",
          cyan: "#00e5ff",
          blue: "#0096ff",
          red: "#ff2244",
          yellow: "#ffcc00",
          orange: "#ff6600",
          purple: "#aa66ff",
        },
        txt: {
          DEFAULT: "#c8e8ff",
          dim: "#6a9bbf",
          faint: "#3a5a7a",
        },
        border: {
          DEFAULT: "#0d2a3e",
          bright: "#1a4060",
        },
      },
      fontFamily: {
        mono: ["'Courier New'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 12px rgba(0,229,255,0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
