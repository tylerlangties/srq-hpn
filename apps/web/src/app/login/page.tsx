import Link from "next/link";

import AppLayout from "../components/AppLayout";

export default function LoginPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="rounded-3xl border border-white/60 bg-white/80 p-8 shadow-sm dark:border-white/10 dark:bg-white/5">
          <h1 className="font-[var(--font-heading)] text-3xl font-semibold md:text-4xl">
            Accounts are coming soon
          </h1>
          <p className="mt-3 text-muted dark:text-white/60">
            Account creation is not available yet, but it is on the roadmap. Existing users can still sign in at
            {" "}
            <Link href="/signin" className="font-semibold text-coral dark:text-purple-300">
              /signin
            </Link>
            .
          </p>
          <p className="mt-2 text-sm text-muted dark:text-white/60">
            Want to learn more about where the project is headed?
            {" "}
            <Link href="/about" className="font-semibold text-charcoal underline-offset-2 hover:underline dark:text-white">
              Visit the About page
            </Link>
            .
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
