import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import AppLayout from "../../components/AppLayout";
import { getArticleBySlug, getArticleSlugs } from "@/lib/articles";

type ArticlePageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateStaticParams() {
  const slugs = await getArticleSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: ArticlePageProps): Promise<Metadata> {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);

  if (!article) {
    return {};
  }

  return {
    title: article.metaTitle ?? article.title,
    description: article.metaDescription ?? article.excerpt,
    openGraph: article.coverImage
      ? {
          title: article.metaTitle ?? article.title,
          description: article.metaDescription ?? article.excerpt,
          images: [{ url: article.coverImage }],
        }
      : undefined,
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { slug } = await params;
  const article = await getArticleBySlug(slug);

  if (!article) {
    notFound();
  }

  return (
    <AppLayout>
      <article className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="mb-8 space-y-4">
          <p className="text-sm uppercase tracking-[0.3em] text-muted dark:text-white/50">
            {article.category}
          </p>
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            {article.title}
          </h1>
          <p className="text-muted dark:text-white/60">{article.excerpt}</p>
          {article.readTime ? (
            <p className="text-sm text-muted dark:text-white/50">
              {article.readTime} read
            </p>
          ) : null}
        </div>
        {article.coverImage ? (
          <div
            className="mb-10 h-64 w-full overflow-hidden rounded-3xl bg-slate-100"
            style={{
              backgroundImage: `url(${article.coverImage})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          />
        ) : null}
        <div className="prose prose-lg max-w-none dark:prose-invert">
          <ReactMarkdown>{article.content}</ReactMarkdown>
        </div>
      </article>
    </AppLayout>
  );
}
