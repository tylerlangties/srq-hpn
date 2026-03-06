"use client";

import { FormEvent, Suspense, useState } from "react";
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

function SignInForm() {
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
        <div className="rounded-3xl border border-white/60 bg-white/80 p-8 shadow-sm dark:border-white/10 dark:bg-white/5">
          <h1 className="font-[var(--font-heading)] text-3xl font-semibold md:text-4xl">Sign in</h1>
          <p className="mt-3 text-muted dark:text-white/60">
            Sign in with your account to continue. Account creation coming soon.
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
                onChange={(event) => setEmail(event.target.value)}
                disabled={disabled}
                className="mt-1 w-full rounded-xl border border-charcoal/15 bg-white/70 px-3 py-2 text-sm dark:border-white/20 dark:bg-white/10"
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
                onChange={(event) => setPassword(event.target.value)}
                disabled={disabled}
                className="mt-1 w-full rounded-xl border border-charcoal/15 bg-white/70 px-3 py-2 text-sm dark:border-white/20 dark:bg-white/10"
              />
            </div>

            {error ? <p className="text-sm text-red-700 dark:text-red-300">{error}</p> : null}

            <button
              type="submit"
              disabled={disabled}
              className="rounded-full bg-charcoal px-5 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
            >
              {status === "submitting" ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </AppLayout>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInForm />
    </Suspense>
  );
}
