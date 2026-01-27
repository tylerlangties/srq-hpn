"use client";

import { useState } from "react";
import AppLayout from "../components/AppLayout";

export default function ContactPage() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (field: "name" | "email" | "message", value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const subject = `Contact from ${form.name || "SRQ Happenings visitor"}`;
    const body = `Name: ${form.name || "N/A"}\nEmail: ${form.email}\n\n${form.message}`;
    const mailto = `mailto:hello@srqhappenings.com?subject=${encodeURIComponent(
      subject
    )}&body=${encodeURIComponent(body)}`;

    window.location.href = mailto;
    setSubmitted(true);
  };

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

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm"
        >
          <div>
            <label
              htmlFor="contact-name"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Name
            </label>
            <input
              id="contact-name"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="Your name"
              value={form.name}
              onChange={(event) => handleChange("name", event.target.value)}
            />
          </div>
          <div>
            <label
              htmlFor="contact-email"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Email
            </label>
            <input
              type="email"
              id="contact-email"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="you@example.com"
              required
              value={form.email}
              onChange={(event) => handleChange("email", event.target.value)}
            />
          </div>
          <div>
            <label
              htmlFor="contact-message"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Message
            </label>
            <textarea
              id="contact-message"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              rows={5}
              placeholder="How can we help?"
              required
              value={form.message}
              onChange={(event) => handleChange("message", event.target.value)}
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-full bg-charcoal px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-charcoal/90 transition dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600"
          >
            Send message
          </button>
          {submitted ? (
            <p className="text-xs text-emerald-700 dark:text-emerald-300">
              Your email client should open with your message pre-filled.
            </p>
          ) : null}
          <p className="text-xs text-muted dark:text-white/40">
            For quick updates, email us at hello@srqhappenings.com.
          </p>
        </form>
      </div>
    </AppLayout>
  );
}
