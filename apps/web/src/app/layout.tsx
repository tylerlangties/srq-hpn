import type { Metadata } from "next";
import {
  Bricolage_Grotesque,
  DM_Sans,
  Space_Grotesk,
  Instrument_Serif,
} from "next/font/google";
import "./globals.css";
import { PostHogProvider } from "./providers/posthog-provider";
import { ThemeProvider } from "./providers/theme-provider";
import { buildSiteUrl, getSiteUrl } from "@/lib/seo";

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
  metadataBase: getSiteUrl(),
  title: "SRQ Happenings",
  description: "Events and happenings in Sarasota",
};

const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "SRQ Happenings",
  url: buildSiteUrl("/").toString(),
};

const websiteJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "SRQ Happenings",
  url: buildSiteUrl("/").toString(),
  inLanguage: "en-US",
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
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
      </head>
      <body
        className={`${bricolage.variable} ${dmSans.variable} ${spaceGrotesk.variable} ${instrumentSerif.variable}`}
      >
        <PostHogProvider>
          <ThemeProvider>{children}</ThemeProvider>
        </PostHogProvider>
      </body>
    </html>
  );
}
