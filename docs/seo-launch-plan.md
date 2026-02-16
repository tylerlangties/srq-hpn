# SRQ Happenings SEO Launch Plan (Maximum Impact)

## Goal

Maximize organic discovery at launch by combining technical SEO, local/event structured data, crawl efficiency, content depth, and measurement.

## Success Metrics (Launch + 30 Days)

- Indexed pages: all priority routes indexed (`/`, `/events`, top event pages, top venue pages, top article pages).
- Impressions and CTR: Search Console impressions trending up week-over-week; CTR >= baseline for branded + local non-branded queries.
- Rich results: valid Event/Article/LocalBusiness structured data with no critical errors.
- Crawl health: no major `404`, `5xx`, blocked canonical pages, or orphaned key pages.

## Priority 0 - Must Ship Before Launch (Hard Blockers)

### 1) Canonical and metadata foundations

- Set `metadataBase` in `apps/web/src/app/layout.tsx` to production origin.
- Ensure canonical URLs on all indexable pages:
  - Home, events list, venue detail, event detail, article detail.
- Add unique title + meta description templates per route type.
- Add Open Graph and Twitter metadata parity (title/description/url/image).

### 2) Crawl controls

- Add `apps/web/src/app/robots.ts`:
  - Allow public routes.
  - Block admin/private/non-SEO surfaces.
  - Reference sitemap URL.
- Add `apps/web/src/app/sitemap.ts`:
  - Include static pages.
  - Include dynamic routes for events, venues, and articles.
  - Include `lastModified` where possible.

### 3) Structured data (JSON-LD)

- Event detail pages: `Event` schema with schedule, location, organizer/source, ticket URL, price/free state, status.
- Venue pages: `Place` or `LocalBusiness` schema with name/address/area/URL.
- Article detail pages: `Article` schema with headline, datePublished, dateModified, author/publisher.
- Site-wide `Organization` + `WebSite` schema in root layout where appropriate.
- Validate with Rich Results Test and Search Console enhancement reports.

### 4) Indexability and rendering quality

- Ensure key SEO pages render meaningful HTML server-side (not client-empty shells for core content).
- Ensure not-found pages return correct status and avoid accidental indexing.
- Ensure canonical redirect logic on event slugs always resolves to one canonical URL.

### 5) Performance and Core Web Vitals baseline

- Optimize LCP on home/events pages:
  - prioritize hero media/text, avoid oversized assets, preconnect critical origins if needed.
- Reduce CLS for cards/lists by reserving dimensions and consistent skeleton heights.
- Keep JS payload lean on indexable entry points.

## Priority 1 - Launch Week (High ROI)

### 6) Internal linking and crawl depth

- Link from homepage and footer to high-value category and venue hubs.
- Add contextual links on event pages:
  - related events at venue,
  - category browse links,
  - article links where relevant.
- Ensure every key page is <= 3 clicks from home.

### 7) Content and query coverage

- Publish location-intent pages/posts for high-value combinations:
  - "things to do in Sarasota this week",
  - "free events in Sarasota",
  - venue/activity-focused guides.
- Standardize event copy quality:
  - concise summary,
  - clear date/time/location,
  - ticket/CTA where available.

### 8) Image SEO

- Ensure descriptive alt text for event/venue/article imagery.
- Use stable, descriptive filenames where controllable.
- Ensure social preview image defaults exist for pages without specific media.

## Priority 2 - Post-Launch Optimization Loop

### 9) Search Console and log-driven iteration

- Submit sitemap in Search Console on launch day.
- Monitor index coverage and fix:
  - duplicate canonicals,
  - soft 404s,
  - blocked resources.
- Track top queries/pages and improve titles/descriptions for low CTR pages.

### 10) Programmatic SEO enhancements

- Add category landing pages with intro copy and faceted internal links.
- Add recurring date-based archive pages (weekend/week/month) if quality can be maintained.
- Add FAQ schema only where genuine Q/A content exists.

## Route-Level SEO Requirements

### Home (`/`)

- Strong local-value title and description.
- Organization/WebSite schema.
- Links to top categories, events, and venues.

### Events list (`/events`)

- Canonicalized query strategy (avoid indexing low-value param combinations).
- Intro text targeting local event-discovery intent.
- Clear internal links to event details and category-focused experiences.

### Event detail (`/events/[slug]`)

- Canonical enforcement for slug variants.
- `Event` schema completeness.
- Distinct title/description from event content.

### Venue detail (`/venues/[slug]`)

- `Place`/`LocalBusiness` schema.
- Human-readable venue summary and upcoming events links.

### Article detail (`/articles/[slug]`)

- `Article` schema.
- Strong publication dates, author/publisher consistency.
- Related links into event and venue ecosystem.

## Launch Checklist (Execution Order)

1. Add `metadataBase`, canonical templates, OG/Twitter parity.
2. Add `sitemap.ts` and `robots.ts` with correct route coverage.
3. Implement JSON-LD for Event, Place/LocalBusiness, Article, Organization.
4. Validate output in Rich Results Test and Search Console live tests.
5. Run Lighthouse on `/`, `/events`, representative `/events/[slug]`, `/venues/[slug]`, `/articles/[slug]`.
6. Fix top CWV and indexing issues.
7. Submit sitemap; monitor daily for first 2 weeks.

## Risk Controls

- Do not index thin/empty pages.
- Do not let filtered URL combinations explode index footprint.
- Do not ship structured data with required fields missing.
- Do not serve conflicting canonical/redirect behavior for event slugs.

## Ownership Suggestion

- Web app: metadata, canonical, JSON-LD rendering, robots/sitemap.
- API/content layer: stable event/venue fields for schema completeness.
- Ops/marketing: Search Console, monitoring, query and CTR iteration.
