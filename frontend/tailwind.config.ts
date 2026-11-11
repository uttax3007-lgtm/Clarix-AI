import type { Config } from "tailwindcss";
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./contexts/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: { bg: "#F5F0E7", bg2: "#EDE5D8", ink: "#35251F", ink2: "#574237", coral: "#F07856", coralHover: "#E86645",
      muted: "#81766D", line: "#DED4C7", surface: "#FFFCF7", ok: "#56856B", warn: "#D99A43", err: "#C9574D" },
    fontFamily: { sans: ["var(--font-inter)", "Noto Sans Devanagari", "sans-serif"],
      head: ["var(--font-jakarta)", "Noto Sans Devanagari", "sans-serif"] } } },
} satisfies Config;
