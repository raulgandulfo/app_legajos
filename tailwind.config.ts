import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: "#1e293b",
        "sidebar-text": "#e2e8f0",
        primary: "#3b82f6",
        "primary-dark": "#2563eb",
        bg: "#eef2f7",
      },
    },
  },
  plugins: [],
};

export default config;
