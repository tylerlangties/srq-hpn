"use client";

import Script from "next/script";

const umamiWebsiteId = process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID;
const umamiScriptSrc = process.env.NEXT_PUBLIC_UMAMI_SCRIPT_URL ?? "https://cloud.umami.is/script.js";

export function UmamiProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      {umamiWebsiteId ? (
        <Script
          defer
          src={umamiScriptSrc}
          data-website-id={umamiWebsiteId}
          strategy="afterInteractive"
        />
      ) : null}
      {children}
    </>
  );
}
