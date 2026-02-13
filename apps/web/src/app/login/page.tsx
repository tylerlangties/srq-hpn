"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import AppLayout from "../components/AppLayout";
import { extractApiStatus, login } from "@/lib/auth";

type LoginStatus = "idle" | "submitting" | "error";

function sanitizeNextPath(next: string | null): string | null {
  if (!next) {
    return null;
  }

  if (!next.startsWith("/") || next.startsWith("//")) {
    return null;
  }

  return next;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<LoginStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("submitting");
    setError(null);

    try {
      const user = await login({ email, password });
      const next = sanitizeNextPath(searchParams.get("next"));

      if (user.role === "admin") {
        router.replace(next || "/admin");
        return;
      }

      router.replace(next || "/");
    } catch (err) {
      const statusCode = extractApiStatus(err);
      if (statusCode === 401) {
        setError("Invalid email or password.");
      } else if (statusCode === 403) {
        setError("Your account is inactive.");
      } else {
        setError(err instanceof Error ? err.message : "Unable to sign in");
      }
      setStatus("error");
    }
  }

  const disabled = status === "submitting";

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-3xl px-6 py-12">
        <div className="rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-8 shadow-sm">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">Sign in</h1>
          <p className="mt-3 text-muted dark:text-white/60">
            Admin access is restricted. Sign in with your account to continue.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-charcoal dark:text-white/80" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={disabled}
                className="mt-1 w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/70 dark:bg-white/10 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-charcoal dark:text-white/80"
                htmlFor="password"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={disabled}
                className="mt-1 w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/70 dark:bg-white/10 px-3 py-2 text-sm"
              />
            </div>

            {error ? <p className="text-sm text-red-700 dark:text-red-300">{error}</p> : null}

            <button
              type="submit"
              disabled={disabled}
              className="rounded-full bg-charcoal text-white px-5 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-60"
            >
              {status === "submitting" ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </AppLayout>
  );
}
