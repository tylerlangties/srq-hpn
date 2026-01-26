import AppLayout from "../components/AppLayout";

export default function SubmitPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Submit an Event
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            Share an event and we’ll review it for inclusion.
          </p>
        </div>

        <form className="space-y-5 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Event title
            </label>
            <input
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="Sunset Jazz on the Bay"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                Date & time
              </label>
              <input
                className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
                placeholder="Fri, 7:30 PM"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
                Location
              </label>
              <input
                className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
                placeholder="Marina Jack"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Description
            </label>
            <textarea
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              rows={4}
              placeholder="Tell us what makes it special..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Contact email
            </label>
            <input
              type="email"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="you@example.com"
            />
          </div>
          <button
            type="button"
            className="w-full rounded-full bg-charcoal px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-charcoal/90 transition dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600"
          >
            Submit for review
          </button>
          <p className="text-xs text-muted dark:text-white/40">
            Submissions are reviewed manually. We’ll reach out if we need more info.
          </p>
        </form>
      </div>
    </AppLayout>
  );
}
