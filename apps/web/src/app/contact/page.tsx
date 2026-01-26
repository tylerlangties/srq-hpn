import AppLayout from "../components/AppLayout";

export default function ContactPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Contact
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            Questions, ideas, or feedback? We’d love to hear from you.
          </p>
        </div>

        <form className="space-y-5 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Name
            </label>
            <input
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Email
            </label>
            <input
              type="email"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-charcoal dark:text-white mb-2">
              Message
            </label>
            <textarea
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              rows={5}
              placeholder="How can we help?"
            />
          </div>
          <button
            type="button"
            className="w-full rounded-full bg-charcoal px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-charcoal/90 transition dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600"
          >
            Send message
          </button>
          <p className="text-xs text-muted dark:text-white/40">
            For quick updates, email us at hello@srqhappenings.com.
          </p>
        </form>
      </div>
    </AppLayout>
  );
}
