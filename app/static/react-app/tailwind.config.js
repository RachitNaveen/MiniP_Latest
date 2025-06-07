/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "var(--border-color)",
        input: "var(--border-color)",
        ring: "var(--primary-color)",
        background: "var(--white-bg)",
        foreground: "var(--dark-text)",
        primary: {
          DEFAULT: "var(--primary-color)",
          foreground: "var(--white-bg)",
        },
        secondary: {
          DEFAULT: "var(--secondary-color)",
          foreground: "var(--white-bg)",
        },
        destructive: {
          DEFAULT: "var(--danger-color)",
          foreground: "var(--white-bg)",
        },
        muted: {
          DEFAULT: "var(--light-bg)",
          foreground: "var(--medium-text)",
        },
        accent: {
          DEFAULT: "var(--light-bg)",
          foreground: "var(--medium-text)",
        },
        card: {
          DEFAULT: "var(--white-bg)",
          foreground: "var(--dark-text)",
        },
      },
      borderRadius: {
        lg: "var(--border-radius)",
        md: "calc(var(--border-radius) - 2px)",
        sm: "calc(var(--border-radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
