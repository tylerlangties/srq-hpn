import type { Metadata } from "next";
import HomePageClient from "./HomePageClient";

const title = "SRQ Happenings | Sarasota Events Today, Tomorrow, and This Weekend";
const description =
  "Discover Sarasota events happening today, tomorrow, and this weekend with local guides and venue details.";
const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";

export const metadata: Metadata = {
  title,
  description,
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title,
    description,
    url: "/",
    type: "website",
    images: [{ url: openGraphImage }],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: [twitterImage],
  },
};

export default function HomePage() {
  return <HomePageClient />;
}
