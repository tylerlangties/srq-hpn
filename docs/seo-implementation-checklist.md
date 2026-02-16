# SRQ Happenings - 3-Step SEO Launch Implementation Checklist

This checklist turns the launch SEO strategy into three implementation phases with clear outcomes, why each phase matters, and what to ship.

## Step 1 - Canonical Foundation (Site Identity + URL Consistency)

**Why this helps**

Search engines need a single, unambiguous site origin and canonical URL structure to index pages correctly. Without this, ranking signals get split across duplicate URLs and crawl budget is wasted.

**What to implement**

- [x] Set a canonical site origin via `metadataBase` in root layout.
- [x] Centralize SEO URL building so robots/sitemap/canonicals all use the same origin.
- [ ] Ensure every indexable route has intentional metadata (title, description, canonical where needed).

**Implementation notes**

- `apps/web/src/app/layout.tsx` now sets `metadataBase` from `NEXT_PUBLIC_SITE_URL` fallback logic.
- `apps/web/src/lib/seo.ts` now provides shared URL helpers (`getSiteUrl`, `buildSiteUrl`) to prevent drift.

## Step 2 - Crawl & Discovery Controls (robots + sitemap)

**Why this helps**

`robots.txt` tells crawlers where they can and cannot go, while `sitemap.xml` tells them what matters most. This improves crawl efficiency and increases the chance that priority pages are discovered and indexed quickly at launch.

**What to implement**

- [x] Add `robots.ts` with allow/disallow rules for public vs non-public surfaces.
- [x] Add sitemap reference in robots output.
- [x] Add `sitemap.ts` with:
  - [x] Static pages (`/`, `/events`, `/venues`, `/articles`, etc.)
  - [x] Dynamic event URLs
  - [x] Dynamic venue URLs
  - [x] Dynamic article URLs
- [ ] Verify sitemap volume and freshness in production runtime.

**Implementation notes**

- `apps/web/src/app/robots.ts` blocks low-value/private surfaces (`/admin`, `/cms`, `/login`) and advertises sitemap.
- `apps/web/src/app/sitemap.ts` includes static and dynamic routes by pulling events and venues from API plus article slugs from content.

## Step 3 - Rich SERP Eligibility (Structured Data + Validation)

**Why this helps**

Structured data increases eligibility for rich results (event details, enhanced snippets), improving visibility and CTR even when ranking position is unchanged.

**What to implement next**

- [ ] Event JSON-LD on `apps/web/src/app/events/[slug]/page.tsx`.
- [ ] Place/LocalBusiness JSON-LD on `apps/web/src/app/venues/[slug]/page.tsx`.
- [ ] Article JSON-LD on `apps/web/src/app/articles/[slug]/page.tsx`.
- [ ] Organization/WebSite JSON-LD in root layout if not already present.
- [ ] Validate all templates with Rich Results Test and fix required fields.

## Launch Verification Gate

Ship Step 3 launch only when all are true:

- [ ] `NEXT_PUBLIC_SITE_URL=https://srqhappenings.com` is set in production env before deploy.
- [ ] `https://<domain>/robots.txt` returns expected rules.
- [ ] `https://<domain>/sitemap.xml` includes key static and dynamic URLs.
- [ ] Search Console sitemap submitted.
- [ ] Representative event/venue/article pages pass structured data validation.
- [ ] No accidental indexing of admin/cms/login paths.

## Social Share Verification (Post-Deploy)

Use this pass after deploy to confirm link previews are correct on major share surfaces.

- [ ] Validate `https://<domain>/` in X Card Validator (title, description, image).
- [ ] Validate `https://<domain>/events` in X Card Validator (title, description, image).
- [ ] Validate one event detail URL in X Card Validator (title, description, image).
- [ ] Validate one article detail URL in X Card Validator (title, description, image).
- [ ] Validate one venue detail URL in X Card Validator (title, description, image).
- [ ] Validate the same representative URLs in Facebook Sharing Debugger and click re-scrape.
- [ ] Validate the same representative URLs in LinkedIn Post Inspector.
- [ ] Paste the same representative URLs in a private Slack or Discord channel and confirm unfurl quality.
- [ ] Verify canonical URL shown in metadata matches expected route for each tested page.

### Share cache playbook

- If previews are stale, trigger platform re-scrape (Facebook/LinkedIn inspectors) and retry.
- Expect platform-level cache delay before all cards update globally.
- If critical pages keep broken previews after re-scrape, treat as release blocker and rollback/patch.

## Search Console Launch-Day Checklist (`srqhappenings.com`)

Use this sequence immediately after production deploy.

1. Open Google Search Console and add property `https://srqhappenings.com`.
2. Verify ownership (DNS TXT preferred for durable verification).
3. Submit sitemap: `https://srqhappenings.com/sitemap.xml`.
4. Run URL Inspection on:
   - `https://srqhappenings.com/`
   - `https://srqhappenings.com/events`
   - one representative event URL
   - one representative venue URL
   - one representative article URL
5. Request indexing for priority URLs after inspection passes.
6. Confirm robots fetch works at `https://srqhappenings.com/robots.txt` and includes sitemap reference.
7. Review Enhancements/Structured Data reports after recrawl and fix any critical errors.
8. Check Coverage report daily for launch week and resolve `404`, `Soft 404`, and duplicate canonical issues.

### Production env snippet

```bash
# .env.production
NEXT_PUBLIC_SITE_URL=https://srqhappenings.com
```
