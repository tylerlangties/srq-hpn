# Big Top Playwright Production Probe + Worker Split Plan

This document is designed for **fast execution** and **AI-assisted implementation later**.

Primary goals:
- Prove whether Playwright can access Big Top from the production droplet.
- Keep risk low (no sweeping changes first).
- Define a clear next-step architecture where only Big Top uses a Playwright-enabled worker image.

---

## 0) Current Problem (Ground Truth)

- Big Top collector currently fails in production with Cloudflare challenge/403.
- Failure occurs before useful scraping work, during bootstrap session/page access.
- Local dev may succeed while production fails due to different egress IP reputation.

Implication:
- This is not a Celery wiring issue.
- This is an anti-bot/network behavior issue.

---

## 1) Phase 1 - Minimal Production Playwright Probe (No App Code Changes)

### 1.1 Scope

Run a tiny Playwright script on the droplet to answer one question:

> Can a real browser session from this production host reach Big Top content reliably?

### 1.2 Non-goals

- No Celery code changes.
- No queue routing changes.
- No Docker Compose service changes.
- No production deployment changes.

### 1.3 Prerequisites

- SSH access to droplet.
- Repo available at `/opt/srq-hpn`.
- Docker installed/running.

### 1.4 Command: One-off Probe Using Official Playwright Image

Run from droplet shell:

```bash
cd /opt/srq-hpn

docker run --rm -i mcr.microsoft.com/playwright/python:v1.55.0-jammy \
python - <<'PY'
from playwright.sync_api import sync_playwright

TARGET_PAGE = "https://www.bigtopbrewing.com/restaurant-brewery-2"
TARGET_DOMAIN = "bigtopbrewing.com"

def looks_like_challenge(html: str, title: str) -> bool:
    text = (html or "").lower()
    t = (title or "").lower()
    markers = [
        "just a moment",
        "cf-challenge",
        "cloudflare",
        "attention required",
    ]
    return any(m in text or m in t for m in markers)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto(TARGET_PAGE, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(3000)

    title = page.title()
    html = page.content()
    current = page.url

    print("TITLE:", title)
    print("URL:", current)
    print("IS_CHALLENGE:", looks_like_challenge(html, title))

    # Optional GraphQL probe from browser context
    result = page.evaluate(
        """
        async () => {
          const query = `query CalendarEventsQuery($restaurantId: Int!) {
            calendarEvents(restaurantId: $restaurantId) {
              count
              records { id name slug createdAt }
            }
          }`;

          const res = await fetch('https://www.bigtopbrewing.com/graphql', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'Origin': 'https://www.bigtopbrewing.com',
              'Referer': 'https://www.bigtopbrewing.com/restaurant-brewery-2'
            },
            body: JSON.stringify({
              query,
              variables: { restaurantId: 36499 }
            })
          });

          const text = await res.text();
          return { status: res.status, sample: text.slice(0, 300) };
        }
        """
    )

    print("GRAPHQL_STATUS:", result["status"])
    print("GRAPHQL_SAMPLE:", result["sample"])

    context.close()
    browser.close()
PY
```

### 1.5 Repeatability Test

Run the same probe at least **5 times** over ~15-30 minutes.

Record for each run:
- `IS_CHALLENGE`
- `GRAPHQL_STATUS`
- elapsed runtime

### 1.6 Pass/Fail Criteria

Pass:
- At least 4/5 runs show `IS_CHALLENGE: False` and `GRAPHQL_STATUS: 200`.

Borderline:
- Mixed success (2-3/5 pass). Playwright may help but reliability is uncertain.

Fail:
- 0-1/5 pass. Browser automation alone is not enough on this egress IP.

### 1.7 Decision Gate

- If Pass -> proceed to Phase 2 (split worker image/queue).
- If Borderline/Fail -> prioritize egress strategy or allowlist/API path before implementation.

---

## 2) Phase 2 - Split Playwright Worker from Normal Celery Worker

This is the implementation plan we discussed earlier: **same droplet**, but separate worker image/service for Big Top only.

### 2.1 Architecture Target

- Keep existing `api`, `celery-worker`, and `celery-beat` for normal tasks.
- Add `celery-worker-browser` service with Playwright dependencies.
- Route only Big Top task to a dedicated queue, e.g. `bigtop_browser`.
- Run browser worker with `--concurrency=1` to protect 2 CPU / 4 GB host.

### 2.2 Why This Split

- Avoid inflating main API/worker images with browser binaries.
- Isolate CPU/RAM impact to one container.
- Limit operational blast radius if browser jobs misbehave.
- Keep all other collectors on lightweight `requests`-based path.

### 2.3 Planned File Changes (When Implementing)

1. `apps/api/app/celery_app.py`
   - Add task route for `app.tasks.collect_bigtop` -> queue `bigtop_browser`.

2. New Dockerfile for browser worker (example: `apps/api/Dockerfile.playwright`)
   - Base from Playwright image or install Playwright + browser in image.
   - Include app code + Python deps + browser deps.

3. `compose.yml`
   - Add `celery-worker-browser` service:
     - command: `celery -A app.celery_app worker -Q bigtop_browser --concurrency=1 --loglevel=INFO`
     - same required env (`DATABASE_URL`, `REDIS_URL`, etc.)

4. Optional: `compose.dev.yml`
   - Add equivalent service if dev parity for browser worker is needed.

### 2.4 Resource Guardrails

- Browser worker concurrency fixed at `1`.
- Keep standard worker concurrency unchanged for other tasks.
- Do not route non-Big Top tasks to browser queue.
- Add hard timeout inside task implementation to avoid stuck browser sessions.

### 2.5 Rollout Steps

1. Build and start browser worker service only.
2. Manually enqueue one Big Top task.
3. Validate logs + DB writes.
4. Run 3-5 manual canary runs.
5. If stable, allow scheduled Big Top task to continue on browser queue.

### 2.6 Rollback Plan

- Stop `celery-worker-browser` service.
- Remove/disable Big Top queue route.
- Revert Big Top to paused/disabled schedule until next approach is ready.

---

## 3) AI Implementation Notes (Explicit)

When implementing from this doc later, follow this order:

1. Add queue routing first.
2. Add browser worker Dockerfile + compose service second.
3. Validate worker boots and registers tasks.
4. Run one manual Big Top task.
5. Confirm task result and DB side effects.
6. Only then enable/keep scheduled execution.

Verification checklist for implementation session:
- `docker compose ... config` succeeds.
- `celery-worker-browser` starts cleanly.
- `inspect registered` includes `app.tasks.collect_bigtop`.
- Manual task execution returns success.
- No regressions in existing non-browser worker tasks.

---

## 4) Quick Command Reference

Manual Big Top task call (current production stack):

```bash
docker compose --env-file .env.production -f compose.yml exec -T celery-worker \
  celery -A app.celery_app call app.tasks.collect_bigtop \
  --kwargs='{"source_id": 5, "future_only": true, "delay": 0.25}'
```

Watch worker logs:

```bash
docker compose --env-file .env.production -f compose.yml logs -f celery-worker
```
