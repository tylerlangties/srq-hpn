import AppLayout from "../components/AppLayout";

export default function LoginPage() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-8 shadow-sm">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Sign in
          </h1>
          <p className="mt-3 text-muted dark:text-white/60">
            Sign-in is coming soon. In the meantime, you can browse events and venues.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
