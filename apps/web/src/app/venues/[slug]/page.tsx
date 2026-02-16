import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import AppLayout from "../../components/AppLayout";
import VenueDetailClient from "./VenueDetailClient";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import { addDays, toYmd } from "@/lib/dates";
import { buildSiteUrl } from "@/lib/seo";
import type { EventOccurrenceOut, VenueDetailOut } from "@/types/events";

type Props = {
  params: Promise<{ slug: string }>;
};

const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";

async function getVenueDetail(slug: string): Promise<VenueDetailOut | null> {
  try {
    return await apiGet<VenueDetailOut>(API_PATHS.venues.detail(slug));
  } catch {
    return null;
  }
}

async function getVenueEvents(
  slug: string,
  start: string,
  end: string
): Promise<EventOccurrenceOut[]> {
  try {
    return await apiGet<EventOccurrenceOut[]>(withQuery(API_PATHS.venues.events(slug), { start, end }));
  } catch {
    return [];
  }
}

function getVenueDescription(venue: VenueDetailOut): string {
  const area = venue.area ?? "Sarasota";
  return `Discover upcoming events at ${venue.name} in ${area}, including venue details and schedules.`;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const venue = await getVenueDetail(slug);

  if (!venue) {
    return {
      title: "Venue not found | SRQ Happenings",
      description: "This venue could not be found.",
      robots: { index: false, follow: true },
    };
  }

  const title = `${venue.name} | SRQ Happenings`;
  const description = getVenueDescription(venue);
  const canonicalPath = `/venues/${venue.slug}`;

  return {
    title,
    description,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      title,
      description,
      url: canonicalPath,
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
}

export default async function VenueDetailPage({ params }: Props) {
  const { slug } = await params;
  const venue = await getVenueDetail(slug);

  if (!venue) {
    notFound();
  }

  if (slug !== venue.slug) {
    redirect(`/venues/${encodeURIComponent(venue.slug)}`);
  }

  const start = toYmd(new Date());
  const end = toYmd(addDays(new Date(), 14));
  const events = await getVenueEvents(venue.slug, start, end);
  const venueJsonLd = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    name: venue.name,
    url: buildSiteUrl(`/venues/${venue.slug}`).toString(),
    sameAs: venue.website ?? undefined,
    address: {
      "@type": "PostalAddress",
      streetAddress: venue.address ?? undefined,
      addressLocality: venue.area ?? "Sarasota",
      addressRegion: "FL",
      addressCountry: "US",
    },
  };

  return (
    <AppLayout>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(venueJsonLd) }}
      />
      <VenueDetailClient venue={venue} events={events} />
    </AppLayout>
  );
}
