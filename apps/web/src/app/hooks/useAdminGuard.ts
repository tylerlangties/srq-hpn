"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { extractApiStatus, getCurrentUser } from "@/lib/auth";
import type { AuthUser } from "@/types/auth";

type AdminGuardState = {
  checking: boolean;
  user: AuthUser | null;
};

export function useAdminGuard(): AdminGuardState {
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function verifyAdmin() {
      try {
        const currentUser = await getCurrentUser();
        if (cancelled) return;

        if (currentUser.role !== "admin") {
          router.replace("/");
          return;
        }

        setUser(currentUser);
      } catch (error) {
        if (cancelled) return;

        const status = extractApiStatus(error);
        if (status === 401) {
          const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
          router.replace(`/login${next}`);
          return;
        }

        router.replace("/");
      } finally {
        if (!cancelled) {
          setChecking(false);
        }
      }
    }

    verifyAdmin();

    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  return { checking, user };
}
