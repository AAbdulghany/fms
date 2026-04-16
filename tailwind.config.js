import tokens from "./src/styles/tailwind.theme.js";

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx,vue,html}",
  ],
  theme: {
    extend: {
      colors: tokens.colors,
      fontFamily: tokens.fontFamily,
      fontSize: tokens.fontSize,
      fontWeight: tokens.fontWeight,
      lineHeight: tokens.lineHeight,
      borderRadius: tokens.borderRadius,
      boxShadow: tokens.boxShadow,
      screens: tokens.screens,
    },
  },
  plugins: [],
};
