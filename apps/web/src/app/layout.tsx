import type { Metadata } from "next";
import {
  Bricolage_Grotesque,
  DM_Sans,
  Space_Grotesk,
  Instrument_Serif,
} from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "./providers/theme-provider";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-bricolage",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-instrument",
});

export const metadata: Metadata = {
  title: "SRQ Happenings",
  description: "Events and happenings in Sarasota",
};

const themeInitScript = `
(() => {
  try {
    const savedTheme = localStorage.getItem("theme");
    const theme =
      savedTheme === "light" || savedTheme === "dark"
        ? savedTheme
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";

    const root = document.documentElement;
    root.dataset.theme = theme;
    root.classList.toggle("dark", theme === "dark");
    root.style.colorScheme = theme;
  } catch {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <style>{`html{background:#F6F1EB;}@media (prefers-color-scheme: dark){html{background:#0a0a0b;}}`}</style>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body
        className={`${bricolage.variable} ${dmSans.variable} ${spaceGrotesk.variable} ${instrumentSerif.variable}`}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
