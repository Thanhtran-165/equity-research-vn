import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // === Fintech Neon Palette (inspired by _viz-shared) ===
        neon: {
          purple: "#a855f7",
          purple2: "#8b5cf6",
          pink: "#ec4899",
          cyan: "#06b6d4",
          green: "#10d98a",
          red: "#ff4d6d",
          amber: "#fbbf24",
        },
        // Dark background layers
        bg: {
          0: "#0a0a14",
          1: "#10101f",
          2: "#16162a",
          3: "#1a1a2e",
        },
        // Light theme fallback (corporate)
        light: {
          bg: "#f8f9fc",
          surface: "#ffffff",
          surface2: "#edf2f7",
          border: "#e2e8f0",
          text: "#1a202c",
          textDim: "#4a5568",
        },
        // Brand accent (kept for backward compat)
        brand: {
          50: "#faf5ff",
          100: "#f3e8ff",
          200: "#e9d5ff",
          300: "#d8b4fe",
          400: "#c084fc",
          500: "#a855f7",
          600: "#9333ea",
          700: "#7e22ce",
          800: "#6b21a8",
          900: "#581c87",
          950: "#3b0764",
        },
        // Semantic
        success: {
          50: "#ecfdf5", 100: "#d1fae5", 500: "#10d98a", 600: "#059669", 700: "#047857",
        },
        warning: {
          50: "#fffbeb", 100: "#fef3c7", 500: "#fbbf24", 600: "#d97706", 700: "#b45309",
        },
        danger: {
          50: "#fef2f2", 100: "#fee2e2", 500: "#ff4d6d", 600: "#e11d48", 700: "#be123c",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        // Glassmorphism
        glass: "0 8px 32px rgba(0,0,0,0.37)",
        "glass-sm": "0 4px 16px rgba(0,0,0,0.2)",
        card: "0 1px 2px 0 rgba(0,0,0,0.04), 0 1px 3px 0 rgba(0,0,0,0.06)",
        "card-hover": "0 8px 32px -4px rgba(168,85,247,0.15), 0 2px 8px -2px rgba(0,0,0,0.1)",
        glow: "0 0 24px rgba(168,85,247,0.3)",
        "glow-pink": "0 0 24px rgba(236,72,153,0.3)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      backgroundImage: {
        "grad-main": "linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
        "grad-cool": "linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%)",
        "grad-bg": "radial-gradient(ellipse at 20% 0%, rgba(139,92,246,0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 100%, rgba(236,72,153,0.12) 0%, transparent 50%)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in-right": "slide-in-right 0.25s ease-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
