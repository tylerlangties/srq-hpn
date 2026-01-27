"use client";

import { useState } from "react";

export default function NewsletterCTA() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email.trim()) return;
    setSubmitted(true);
    setEmail("");
  };

  return (
    <section className="py-12 mb-8">
      <div className="rounded-3xl bg-gradient-to-r from-coral/15 via-white/80 to-gulf/15 border border-white/60 p-8 md:p-12 shadow-xl fade-up delay-1 dark:bg-gradient-to-r dark:from-purple-600/10 dark:via-white/5 dark:to-pink-600/10 dark:border-white/10 dark:backdrop-blur-sm">
        <div className="grid gap-8 md:grid-cols-[1.2fr_0.8fr] items-center">
          <div>
            <h2 className="text-2xl md:text-3xl font-[var(--font-heading)] font-semibold mb-3">
              Get the weekend guide
            </h2>
            <p className="text-muted dark:text-white/60 max-w-md">
              Every Thursday, we send a curated list of the best things to do this
              weekend. Short, sweet, and practical.
            </p>
            {submitted ? (
              <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-300">
                Thanks! You&apos;re on the list.
              </p>
            ) : null}
          </div>
          <form
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row gap-3"
          >
            <input
              type="email"
              placeholder="your@email.com"
              className="flex-1 rounded-full border border-white/70 bg-white/90 px-5 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-coral/30 dark:border-white/20 dark:bg-white/5 dark:text-white dark:placeholder-white/40 dark:focus:ring-purple-500/20"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <button
              type="submit"
              className="rounded-full bg-charcoal px-7 py-3.5 text-sm font-semibold text-white shadow-lg hover:bg-charcoal/90 transition whitespace-nowrap dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600 dark:shadow-purple-500/25"
            >
              Subscribe
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
