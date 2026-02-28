"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CONTENT_API_PATHS, withQuery } from "@/lib/api-paths";
import { SHARED_RESPONSIVE } from "@/lib/responsive";
import type { ArticleSummary } from "@/types/articles";

type Props = {
  showHeader?: boolean;
  limit?: number;
};

const fallbackGradient = "linear-gradient(135deg, #FF7A5C 0%, #ffd27f 100%)";

export default function ArticlesSection({ showHeader = true, limit }: Props) {
  const resolvedLimit = useMemo(() => {
    if (typeof limit === "number") {
      return limit;
    }
    return showHeader ? 3 : undefined;
  }, [limit, showHeader]);
  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadArticles() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(withQuery(CONTENT_API_PATHS.articles, { limit: resolvedLimit }), {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Failed to load articles.");
        }

        const payload = (await response.json()) as {
          articles: ArticleSummary[];
        };

        setArticles(payload.articles);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError("Unable to load articles right now.");
        }
      } finally {
        setLoading(false);
      }
    }

    void loadArticles();

    return () => {
      controller.abort();
    };
  }, [resolvedLimit]);

  const placeholderCount = resolvedLimit ?? 3;

  return (
    <section className="py-12">
      {showHeader ? (
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl md:text-3xl font-[var(--font-heading)] font-semibold mb-2">
              Articles & Guides
            </h2>
            <p className="text-muted dark:text-white/50">
              Discover the best of Sarasota through local stories
            </p>
          </div>
          <Link
            href="/articles"
            className={`${SHARED_RESPONSIVE.desktopOnlyBlock} rounded-full border border-charcoal/10 bg-white/80 px-5 py-2.5 text-sm font-medium text-charcoal hover:bg-white transition dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10`}
          >
            All articles
          </Link>
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-muted dark:text-white/50">{error}</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-3">
          {loading
            ? Array.from({ length: placeholderCount }).map((_, index) => (
                <div
                  key={`article-skeleton-${index}`}
                  className="h-80 rounded-2xl border border-white/60 bg-white/80 shadow-lg shadow-charcoal/5 animate-pulse dark:border-white/10 dark:bg-white/5"
                />
              ))
            : articles.map((article) => (
                <Link
                  key={article.slug}
                  href={`/articles/${article.slug}`}
                  className="block h-full"
                >
                  <article className="group flex h-full min-h-80 cursor-pointer flex-col overflow-hidden rounded-2xl border border-white/60 bg-white/80 shadow-lg shadow-charcoal/5 transition-all hover:translate-y-[-2px] hover:shadow-xl dark:border-white/10 dark:bg-white/5 dark:hover:border-white/20 dark:hover:shadow-purple-500/5">
                    <div
                      className="h-36 w-full"
                      style={
                        article.coverImage
                          ? {
                              backgroundImage: `url(${article.coverImage})`,
                              backgroundSize: "cover",
                              backgroundPosition: "center",
                            }
                          : { background: fallbackGradient }
                      }
                    />
                    <div className="flex flex-1 flex-col gap-2 p-4">
                      <div className="flex items-center gap-3">
                        <span className="max-w-[11rem] truncate rounded-full bg-sand px-3 py-1 text-xs font-semibold text-charcoal dark:bg-white/10 dark:text-white">
                          {article.category}
                        </span>
                        {article.readTime ? (
                          <span className="text-xs text-muted dark:text-white/60">
                            {article.readTime} read
                          </span>
                        ) : null}
                      </div>
                      <h3 className="line-clamp-2 font-semibold leading-snug text-charcoal transition group-hover:text-coral dark:text-white dark:group-hover:text-purple-300">
                        {article.title}
                      </h3>
                      <p className="text-sm text-muted line-clamp-3 dark:text-white/50">
                        {article.excerpt}
                      </p>
                    </div>
                  </article>
                </Link>
              ))}
          {!loading && articles.length === 0 ? (
            <p className="text-sm text-muted dark:text-white/50">
              No articles published yet.
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
