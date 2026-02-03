import AppLayout from "../components/AppLayout";

export default function AboutPage() {
  const roadmapItems = [
    {
      title: "Accounts and a weekly digest",
      description:
        "Create an account, pick your interests, and get a calm weekly email with events you actually want.",
    },
    {
      title: "More event sources, more organizers!",
      description:
        "Expand the mix of venues and community partners so the calendar feels more complete and diverse.",
    },
    {
      title: "Community submissions that feel easy",
      description:
        "A smoother submit flow with clear status updates so organizers know when their event is live.",
    },
    {
      title: "Organizer tools",
      description:
        "Simple tools to manage venues, recurring events, and one-off popups without the hassle.",
    },
  ];

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
              A note from the builder
            </h2>
            <p className="mt-3 text-muted dark:text-white/60 leading-relaxed">
              I built SRQ Happenings because I wanted a friendly, low-stress way to
              keep up with local events without bouncing between a dozen calendars.
              I’m the sole developer and maintainer, and I care a lot about keeping
              this site warm, welcoming, and useful for real life planning.
            </p>
            <p className="mt-3 text-muted dark:text-white/60 leading-relaxed">
              If you host events, send them in. If you’re just browsing, I hope you
              find something that makes your week a little brighter.
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

          <section className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-2xl font-[var(--font-heading)] font-semibold">
                  Roadmap
                </h2>
                <p className="mt-2 text-muted dark:text-white/60 leading-relaxed">
                  What I’m working on next, shaped by community feedback and real
                  needs.
                </p>
              </div>
              <span className="inline-flex w-fit items-center rounded-full border border-white/60 dark:border-white/10 bg-white/70 dark:bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-muted dark:text-white/60">
                Coming soon
              </span>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {roadmapItems.map((item) => (
                <div
                  key={item.title}
                  className="rounded-2xl border border-white/60 dark:border-white/10 bg-white/70 dark:bg-white/5 p-4 shadow-sm"
                >
                  <h3 className="text-lg font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm text-muted dark:text-white/60 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </AppLayout>
  );
}
