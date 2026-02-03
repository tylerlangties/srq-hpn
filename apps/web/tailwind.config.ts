import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sand: "#F6F1EB",       // warm beach sand
        cloud: "#FCFBF9",      // off-white / paper
        gulf: "#1FB6B2",       // teal gulf water
        coral: "#FF7A5C",      // sunset coral
        palm: "#3A7F6B",       // coastal green
        charcoal: "#2F2F2F",  // soft black
        muted: "#6B6B6B",     // secondary text
      },
    },
  },
  plugins: [typography],
};

export default config;
