import type { Metadata } from "next";
import VenuesPageClient from "./VenuesPageClient";

const title = "Sarasota Venues | SRQ Happenings";
const description =
  "Browse Sarasota venues hosting live music, arts, food, and community events across the city.";
const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";

export const metadata: Metadata = {
  title,
  description,
  alternates: {
    canonical: "/venues",
  },
  openGraph: {
    title,
    description,
    url: "/venues",
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

export default function VenuesPage() {
  return <VenuesPageClient />;
}
