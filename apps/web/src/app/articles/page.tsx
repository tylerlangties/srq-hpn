import type { Metadata } from "next";
import AppLayout from "../components/AppLayout";
import ArticlesSection from "../components/home/ArticlesSection";

const title = "Sarasota Guides and Local Articles | SRQ Happenings";
const description =
  "Read Sarasota local guides, event roundups, and neighborhood stories to plan your week.";
const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";

export const metadata: Metadata = {
  title,
  description,
  alternates: {
    canonical: "/articles",
  },
  openGraph: {
    title,
    description,
    url: "/articles",
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

export default function ArticlesPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Articles & Guides
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            Local stories, weekend roundups, and Sarasota guides.
          </p>
        </div>

        <ArticlesSection showHeader={false} />
      </div>
    </AppLayout>
  );
}
