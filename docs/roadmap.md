---
name: SRQ Happenings Launch Roadmap (Updated)
overview: Launch-optimized roadmap with completed work checked off, current gaps prioritized, and post-launch initiatives preserved as the final step.
todos: []
updated: 2026-02-16
---

# SRQ Happenings: Launch Roadmap (Updated)

This roadmap replaces stale assumptions with current implementation status, marks completed items, and re-orders remaining work for fastest path to launch.

---

## Current status snapshot (from codebase)

### Completed foundations

- [x] Monorepo structure in place (`apps/api`, `apps/web`), with Docker dev and prod compose files.
- [x] Articles are content-backed (markdown files + loader + list/detail pages), no longer mock-only.
- [x] Celery app and task scaffolding exist with scheduled jobs in dev.
- [x] Admin auth and roles are implemented (login/logout/me, protected admin routes).
- [x] Event detail page and API flow exist, including canonical route resolution.
- [x] "Events this week" count endpoint exists and is wired to homepage hero.
- [x] Category models and ingestion category assignment logic exist.

### Partially complete / launch gaps

- [x] Venue dynamic route reliability fix for Next.js async params handling.
- [x] Category API and end-to-end category filtering (API + UI + footer links).
- [x] "Surprise me" endpoint and CTA behavior (currently links to `/events`).
- [x] Sitemap, robots, and structured data (JSON-LD) for SEO completeness.
- [x] Analytics integration (PostHog) and launch event instrumentation.
- [ ] CI/CD workflows for repeatable checks and deploy readiness.
- [ ] Production background job strategy parity (prod compose currently does not include Redis/Celery worker/beat).

### De-prioritized before launch

- [ ] Full organizer/auth/newsletter ecosystem and advanced personalization (kept in final step).

---

## Step 1: Launch blockers (stability and correctness)

**Goal:** Remove known route/runtime risks so core browsing works reliably on launch day.

- [x] Fix venue route params handling in `apps/web/src/app/venues/[slug]/page.tsx` to follow current Next.js dynamic route conventions.
- [x] Verify venue 404/empty states and ensure they are clear and navigable.
- [x] Smoke-check event detail canonical redirects/route resolution behavior in `apps/web/src/app/events/[slug]/page.tsx` and API resolver.

**Deliverables:** Venue pages stable in production runtime; event detail route behavior confirmed.

---

## Step 2: Event discovery completion (highest product impact)

**Goal:** Make event discovery fully functional via categories, filters, and surprise flow.

### 2.1 Categories API and filters

- [x] Add `GET /api/categories` (id, name, slug).
- [x] Extend `GET /api/events/range` (and optionally `/day`) with category/free/venue filter params.
- [x] Ensure category info is consistently included in event response payloads for list/detail use.

### 2.2 Frontend filtering and footer wiring

- [x] Wire events page filters to backend query params (date range, category, free-only).
- [x] Replace static footer category links with filtered links (`/events?category={slug}`) or agreed route pattern.
- [x] Align footer labels with canonical category slugs returned by API.

### 2.3 Surprise me

- [x] Add `GET /api/events/surprise?days=7` (optional category param).
- [x] Update hero CTA to fetch surprise result and navigate to event detail route.

**Deliverables:** End-to-end event discovery experience is complete and functional.

---

## Step 3: SEO launch minimum

**Goal:** Ensure discoverability at launch with crawl/index/share basics.

- [x] Add `apps/web/src/app/sitemap.ts` (static + dynamic routes).
- [x] Add `apps/web/src/app/robots.ts` (allow/disallow + sitemap reference).
- [x] Set/verify `metadataBase` in root layout for canonical URL generation.
- [ ] Add JSON-LD:
  - [x] Event schema on event detail pages
  - [x] Place/LocalBusiness schema on venue pages
  - [x] Article schema on article detail pages
- [ ] Validate metadata and structured data outputs before launch.

**Deliverables:** Crawlable and share-ready pages with structured data coverage.

---

## Step 4: Analytics and launch instrumentation

**Goal:** Capture baseline product usage and monetization signals from day one.

- [x] Integrate PostHog (cookieless mode) into web app.
- [x] Instrument key events:
  - [x] `event_viewed`
  - [x] `event_link_clicked`
  - [x] `featured_event_impression`
  - [x] `featured_event_clicked`
- [ ] Create initial dashboard (daily users, top events, top referrers, device split).

**Deliverables:** Working analytics with actionable baseline dashboard.

---

## Step 5: Deployment readiness and operations

**Goal:** Make launch reproducible, supportable, and safe.

### 5.1 Production background jobs parity

- [ ] Decide and implement production strategy for Redis + Celery worker/beat (compose or external service).
- [ ] Ensure scheduled scraping/weather tasks run in production context.

### 5.2 CI/CD

- [ ] Add GitHub Actions workflows for PR/push checks:
  - [ ] API lint/tests
  - [ ] Web lint/build
- [ ] Add release/deploy workflow (or documented deploy runbook if manual for v1).

### 5.3 Runbook and cost notes

- [x] Base infra/runbook docs exist (`docs/database-guide.md`).
- [x] Add final launch runbook checklist (migrations, rollback, logs, backups).
- [ ] Add/update projected monthly cost section for selected hosting stack.

**Deliverables:** Repeatable deploy path, production job execution, launch runbook.

---

## Step 6: Nice-to-have polish before/just after launch

**Goal:** Improve quality and consistency without blocking go-live.

- [ ] Event card visual consistency pass (grid sizing, responsive parity).
- [ ] UI consistency pass (spacing, loading states, empty/error states wording).
- [ ] Scraper CLI contract normalization final pass (ensure all collectors accept documented shared flags).

**Deliverables:** Better UX consistency and cleaner collector ergonomics.

---

## Step 7 (Next sprint, post-launch): Long-term improvements

**Goal:** Expand product depth after launch stability and discovery loops are validated.

| Area | Details |
|------|--------|
| **Venue matching** | Improve matching of new occurrences to venues using aliases + similarity scoring to reduce admin/manual resolution workload. |
| **Sign-in and newsletter** | User accounts, preference capture, and weekly digest delivery pipeline. |
| **Event source expansion** | Add more scrapers/feeds and register/schedule through Celery tasks. |
| **Submit form backend** | Convert submit flow from mailto to API + moderation queue in admin. |
| **Organizers** | Organizer role, self-service venue management, and event/ical upload workflows. |
| **Personalization** | Better personalized recommendations and robust user-facing fallback/error copy patterns. |
| **Social share QA** | Post-deploy preview validation for `/`, `/events`, one event detail, one article detail, and one venue detail using X Card Validator, Facebook Sharing Debugger (with re-scrape), LinkedIn Post Inspector, plus a private Slack/Discord unfurl check. Verify title, description, canonical URL, and image render consistently. |
| **Share cache monitoring** | Add a lightweight playbook for stale previews (force re-scrape, expected cache delays, and rollback trigger if critical cards break). |

**Deliverables:** Prioritized implementation backlog and first post-launch sprint tickets.

---

## Completed work checklist (quick reference)

- [x] Content-backed articles pipeline and article detail pages.
- [x] Celery app + task definitions + scheduled dev jobs.
- [x] Dockerized local stack for API/Web/DB/Redis/Celery.
- [x] Admin auth/role enforcement.
- [x] Event detail API/route and card linking.
- [x] Homepage live events count endpoint integration.
- [x] Category domain model and ingestion category assignment.
- [x] PostHog Cloud analytics integration and launch event instrumentation.

---

## Recommended launch sequence

1. Step 1 (stability blockers)
2. Step 2 (discovery completeness)
3. Step 3 (SEO minimum)
4. Step 4 (analytics)
5. Step 5 (ops/CI/CD)
6. Step 6 (polish)
7. Step 7 (post-launch)

This order maximizes launch success by prioritizing reliability and core discovery flows before expansion work.
