export type ArticleSummary = {
  slug: string;
  title: string;
  excerpt: string;
  category: string;
  readTime?: string;
  coverImage?: string;
  date?: string;
  metaTitle?: string;
  metaDescription?: string;
};

export type ArticleDetail = ArticleSummary & {
  content: string;
};
