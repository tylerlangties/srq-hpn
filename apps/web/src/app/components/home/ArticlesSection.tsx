import Link from "next/link";

type Article = {
  id: number;
  title: string;
  excerpt: string;
  category: string;
  readTime: string;
  image: string;
};

const MOCK_ARTICLES: Article[] = [
  {
    id: 1,
    title: "10 Hidden Gems for Date Night in Sarasota",
    excerpt:
      "From rooftop cocktails to moonlit beach walks, discover romantic spots locals love.",
    category: "Guide",
    readTime: "5 min",
    image: "linear-gradient(135deg, #FF7A5C 0%, #ffd27f 100%)",
  },
  {
    id: 2,
    title: "Family-Friendly Events This Weekend",
    excerpt: "Activities that'll keep the kids happy and give parents a break.",
    category: "Family",
    readTime: "3 min",
    image: "linear-gradient(135deg, #1FB6B2 0%, #3A7F6B 100%)",
  },
  {
    id: 3,
    title: "The Best Free Things to Do in SRQ",
    excerpt: "Explore Sarasota without spending a dime – beaches, parks, and public art.",
    category: "Budget",
    readTime: "4 min",
    image: "linear-gradient(135deg, #3A7F6B 0%, #1FB6B2 100%)",
  },
];

type Props = {
  showHeader?: boolean;
};

export default function ArticlesSection({ showHeader = true }: Props) {
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
            className="hidden sm:block rounded-full border border-charcoal/10 bg-white/80 px-5 py-2.5 text-sm font-medium text-charcoal hover:bg-white transition dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
          >
            All articles
          </Link>
        </div>
      ) : null}

      <div className="grid gap-6 md:grid-cols-3">
        {MOCK_ARTICLES.map((article) => (
          <Link key={article.id} href="/articles" className="block">
            <article className="group rounded-2xl bg-white/80 border border-white/60 overflow-hidden shadow-lg shadow-charcoal/5 hover:shadow-xl hover:translate-y-[-2px] transition-all cursor-pointer dark:bg-white/5 dark:border-white/10 dark:hover:border-white/20 dark:hover:shadow-purple-500/5">
              <div className="h-40 w-full" style={{ background: article.image }}></div>
              <div className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="rounded-full bg-sand px-3 py-1 text-xs font-semibold text-charcoal dark:bg-white/10 dark:text-white">
                    {article.category}
                  </span>
                  <span className="text-xs text-muted dark:text-white/40">
                    {article.readTime} read
                  </span>
                </div>
                <h3 className="font-semibold text-charcoal mb-2 group-hover:text-coral transition leading-snug dark:text-white dark:group-hover:text-purple-300">
                  {article.title}
                </h3>
                <p className="text-sm text-muted dark:text-white/50 line-clamp-2">
                  {article.excerpt}
                </p>
              </div>
            </article>
          </Link>
        ))}
      </div>
    </section>
  );
}
