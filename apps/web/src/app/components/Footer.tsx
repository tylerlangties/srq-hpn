import Link from "next/link";

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-white/50 dark:border-white/10 bg-white/50 dark:bg-black/40 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-coral to-gulf text-white font-bold text-sm dark:from-purple-500 dark:to-pink-500">
                SRQ
              </div>
              <span className="font-[var(--font-heading)] text-lg font-semibold">
                Happenings
              </span>
            </div>
            <p className="text-sm text-muted dark:text-white/50">
              Your guide to everything happening in Sarasota.
            </p>
          </div>
          <div>
            <p className="font-semibold text-charcoal dark:text-white mb-4">Explore</p>
            <div className="space-y-2 text-sm text-muted dark:text-white/50">
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Events
              </Link>
              <Link href="/venues" className="hover:text-charcoal dark:hover:text-white transition block">
                Venues
              </Link>
              <Link href="/articles" className="hover:text-charcoal dark:hover:text-white transition block">
                Articles
              </Link>
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Calendar
              </Link>
            </div>
          </div>
          <div>
            <p className="font-semibold text-charcoal dark:text-white mb-4">Categories</p>
            <div className="space-y-2 text-sm text-muted dark:text-white/50">
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Music
              </Link>
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Arts & Culture
              </Link>
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Food & Drink
              </Link>
              <Link href="/events" className="hover:text-charcoal dark:hover:text-white transition block">
                Outdoors
              </Link>
            </div>
          </div>
          <div>
            <p className="font-semibold text-charcoal dark:text-white mb-4">Connect</p>
            <div className="space-y-2 text-sm text-muted dark:text-white/50">
              <Link href="/submit" className="hover:text-charcoal dark:hover:text-white transition block">
                Submit Event
              </Link>
              <Link href="/contact" className="hover:text-charcoal dark:hover:text-white transition block">
                Contact
              </Link>
              <Link href="/about" className="hover:text-charcoal dark:hover:text-white transition block">
                About
              </Link>
            </div>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-charcoal/10 dark:border-white/10 text-center text-sm text-muted dark:text-white/40">
          © 2026 SRQ Happenings. Made with ☀️ in Sarasota.
        </div>
      </div>
    </footer>
  );
}
