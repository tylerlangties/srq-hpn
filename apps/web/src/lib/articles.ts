import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";
import type { ArticleDetail, ArticleSummary } from "@/types/articles";

type ArticleFrontmatter = {
  title?: string;
  excerpt?: string;
  category?: string;
  readTime?: string;
  coverImage?: string;
  date?: string;
  metaTitle?: string;
  metaDescription?: string;
};

type ArticleOptions = {
  limit?: number;
};

const articlesDirectory = path.join(process.cwd(), "content", "articles");

function toArticleSummary(
  slug: string,
  frontmatter: ArticleFrontmatter
): ArticleSummary {
  return {
    slug,
    title: frontmatter.title ?? "Untitled",
    excerpt: frontmatter.excerpt ?? "",
    category: frontmatter.category ?? "Guide",
    readTime: frontmatter.readTime,
    coverImage: frontmatter.coverImage,
    date: frontmatter.date,
    metaTitle: frontmatter.metaTitle,
    metaDescription: frontmatter.metaDescription,
  };
}

function toArticleDetail(
  slug: string,
  frontmatter: ArticleFrontmatter,
  content: string
): ArticleDetail {
  return {
    ...toArticleSummary(slug, frontmatter),
    content,
  };
}

function sortByDateDesc(a: ArticleSummary, b: ArticleSummary) {
  const aTime = a.date ? new Date(a.date).getTime() : 0;
  const bTime = b.date ? new Date(b.date).getTime() : 0;
  return bTime - aTime;
}

export async function getArticleSlugs(): Promise<string[]> {
  const entries = await fs.readdir(articlesDirectory);
  return entries.filter((entry) => entry.endsWith(".md")).map((entry) => entry.replace(/\.md$/, ""));
}

export async function getArticleSummaries(
  options: ArticleOptions = {}
): Promise<ArticleSummary[]> {
  const entries = await fs.readdir(articlesDirectory);
  const articles = await Promise.all(
    entries
      .filter((entry) => entry.endsWith(".md"))
      .map(async (entry) => {
        const slug = entry.replace(/\.md$/, "");
        const filePath = path.join(articlesDirectory, entry);
        const file = await fs.readFile(filePath, "utf-8");
        const { data } = matter(file);
        return toArticleSummary(slug, data as ArticleFrontmatter);
      })
  );

  const sorted = articles.sort(sortByDateDesc);

  if (typeof options.limit === "number") {
    return sorted.slice(0, options.limit);
  }

  return sorted;
}

export async function getArticleBySlug(
  slug: string
): Promise<ArticleDetail | null> {
  try {
    const filePath = path.join(articlesDirectory, `${slug}.md`);
    const file = await fs.readFile(filePath, "utf-8");
    const { data, content } = matter(file);
    return toArticleDetail(slug, data as ArticleFrontmatter, content);
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}
