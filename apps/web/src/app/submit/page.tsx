"use client";

import { useState } from "react";
import AppLayout from "../components/AppLayout";

export default function SubmitPage() {
  const [form, setForm] = useState({
    title: "",
    dateTime: "",
    location: "",
    description: "",
    email: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    field: "title" | "dateTime" | "location" | "description" | "email",
    value: string
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const subject = `Event submission: ${form.title || "New event"}`;
    const body = [
      `Title: ${form.title || "N/A"}`,
      `Date & Time: ${form.dateTime || "N/A"}`,
      `Location: ${form.location || "N/A"}`,
      `Contact Email: ${form.email || "N/A"}`,
      "",
      "Description:",
      form.description || "N/A",
    ].join("\n");

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
            Submit an Event
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            Share an event and we’ll review it for inclusion.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm"
        >
          <div>
            <label
              htmlFor="submit-title"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Event title
            </label>
            <input
              id="submit-title"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="Sunset Jazz on the Bay"
              required
              value={form.title}
              onChange={(event) => handleChange("title", event.target.value)}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label
                htmlFor="submit-date"
                className="block text-sm font-medium text-charcoal dark:text-white mb-2"
              >
                Date & time
              </label>
              <input
                id="submit-date"
                className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
                placeholder="Fri, 7:30 PM"
                required
                value={form.dateTime}
                onChange={(event) => handleChange("dateTime", event.target.value)}
              />
            </div>
            <div>
              <label
                htmlFor="submit-location"
                className="block text-sm font-medium text-charcoal dark:text-white mb-2"
              >
                Location
              </label>
              <input
                id="submit-location"
                className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
                placeholder="Marina Jack"
                value={form.location}
                onChange={(event) => handleChange("location", event.target.value)}
              />
            </div>
          </div>
          <div>
            <label
              htmlFor="submit-description"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Description
            </label>
            <textarea
              id="submit-description"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              rows={4}
              placeholder="Tell us what makes it special..."
              value={form.description}
              onChange={(event) => handleChange("description", event.target.value)}
            />
          </div>
          <div>
            <label
              htmlFor="submit-email"
              className="block text-sm font-medium text-charcoal dark:text-white mb-2"
            >
              Contact email
            </label>
            <input
              type="email"
              id="submit-email"
              className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-white/90 dark:bg-white/5 px-4 py-3 text-sm dark:text-white"
              placeholder="you@example.com"
              required
              value={form.email}
              onChange={(event) => handleChange("email", event.target.value)}
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-full bg-charcoal px-6 py-3 text-sm font-semibold text-white shadow-lg hover:bg-charcoal/90 transition dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600"
          >
            Submit for review
          </button>
          {submitted ? (
            <p className="text-xs text-emerald-700 dark:text-emerald-300">
              Your email client should open with the submission details.
            </p>
          ) : null}
          <p className="text-xs text-muted dark:text-white/60">
            Submissions are reviewed manually. We’ll reach out if we need more info.
          </p>
        </form>
      </div>
    </AppLayout>
  );
}
