import AppLayout from "../components/AppLayout";

export default function AboutPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-4xl px-6 py-12">
        <div className="mb-10">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            About SRQ Happenings
          </h1>
          <p className="mt-3 text-muted dark:text-white/60">
            A local guide to events, arts, food, and weekend plans in Sarasota.
          </p>
        </div>

        <div className="space-y-8">
          <section className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
            <h2 className="text-2xl font-[var(--font-heading)] font-semibold">
              Our mission
            </h2>
            <p className="mt-3 text-muted dark:text-white/60 leading-relaxed">
              We make it easy to find what’s happening in Sarasota without
              overwhelming you. Our goal is to be a calm, curated guide for locals
              and visitors alike.
            </p>
          </section>

          <section className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
            <h2 className="text-2xl font-[var(--font-heading)] font-semibold">
              How it works
            </h2>
            <p className="mt-3 text-muted dark:text-white/60 leading-relaxed">
              We aggregate trusted sources and highlight the best of the week. If
              you host an event, submit it and we’ll review it for inclusion.
            </p>
          </section>

          <section className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
            <h2 className="text-2xl font-[var(--font-heading)] font-semibold">
              Get involved
            </h2>
            <p className="mt-3 text-muted dark:text-white/60 leading-relaxed">
              Share feedback, submit events, or partner with us on local
              initiatives. We’re building this with the community.
            </p>
          </section>
        </div>
      </div>
    </AppLayout>
  );
}
