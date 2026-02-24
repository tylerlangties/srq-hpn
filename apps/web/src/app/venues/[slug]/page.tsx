import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import AppLayout from "../../components/AppLayout";
import VenueDetailClient from "./VenueDetailClient";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import { addDays, toYmd } from "@/lib/dates";
import { buildSiteUrl } from "@/lib/seo";
import type { EventOccurrenceOut, VenueDetailOut, VenueOut } from "@/types/events";

type Props = {
  params: Promise<{ slug: string }>;
};

const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";
const venuePageRevalidateSeconds = 900;
const venueEventsRevalidateSeconds = 300;

export const revalidate = 900;

async function getVenueSlugs(): Promise<string[]> {
  try {
    const venues = await apiGet<VenueOut[]>(API_PATHS.venues.list, {
      revalidate: venuePageRevalidateSeconds,
      tags: ["venues"],
    });
    return venues.map((venue) => venue.slug);
  } catch {
    return [];
  }
}

export async function generateStaticParams() {
  const slugs = await getVenueSlugs();
  return slugs.map((slug) => ({ slug }));
}

function normalizeVenueImagePath(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }

  const trimmed = path.trim();
  if (!trimmed) {
    return null;
  }

  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}

function toPlainTextFromMarkdown(markdown: string | null | undefined): string {
  if (!markdown) {
    return "";
  }

  return markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/[*_~>#-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function getVenueDetail(slug: string): Promise<VenueDetailOut | null> {
  try {
    return await apiGet<VenueDetailOut>(API_PATHS.venues.detail(slug), {
      revalidate: venuePageRevalidateSeconds,
      tags: ["venues", `venue:${slug}`],
    });
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
    return await apiGet<EventOccurrenceOut[]>(withQuery(API_PATHS.venues.events(slug), { start, end }), {
      revalidate: venueEventsRevalidateSeconds,
      tags: [`venue:${slug}:events`],
    });
  } catch {
    return [];
  }
}

function getVenueDescription(venue: VenueDetailOut): string {
  if (venue.description?.trim()) {
    const trimmed = venue.description.trim();
    return trimmed.length > 160 ? `${trimmed.slice(0, 157)}...` : trimmed;
  }

  const markdownText = toPlainTextFromMarkdown(venue.description_markdown);
  if (markdownText) {
    return markdownText.length > 160 ? `${markdownText.slice(0, 157)}...` : markdownText;
  }

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
  const heroImagePath = normalizeVenueImagePath(venue.hero_image_path);
  const venueOpenGraphImage = heroImagePath
    ? buildSiteUrl(heroImagePath).toString()
    : openGraphImage;
  const venueTwitterImage = heroImagePath
    ? buildSiteUrl(heroImagePath).toString()
    : twitterImage;

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
      images: [{ url: venueOpenGraphImage }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [venueTwitterImage],
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
  const heroImagePath = normalizeVenueImagePath(venue.hero_image_path);
  const markdownDescription = toPlainTextFromMarkdown(venue.description_markdown);
  const jsonLdDescription = venue.description ?? (markdownDescription || undefined);
  const venueJsonLd = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    name: venue.name,
    description: jsonLdDescription,
    image: heroImagePath ? [buildSiteUrl(heroImagePath).toString()] : undefined,
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
