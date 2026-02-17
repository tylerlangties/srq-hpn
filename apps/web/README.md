This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Analytics

This app uses PostHog Cloud (`posthog-js`) for Step 4 launch instrumentation.

Currently implemented events:

- `event_viewed`
- `event_link_clicked`
- `featured_event_impression`
- `featured_event_clicked`

Common event properties include `source` and optional venue fields (`venue_id`, `venue_slug`, `venue_name`).

Required env vars:

```bash
NEXT_PUBLIC_POSTHOG_KEY=<posthog_project_key>
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
NEXT_PUBLIC_ANALYTICS_DEBUG=false
```

If `NEXT_PUBLIC_POSTHOG_KEY` is not set, analytics events are not sent.

Set `NEXT_PUBLIC_ANALYTICS_DEBUG=true` for local development to log each tracked event to the browser console.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
