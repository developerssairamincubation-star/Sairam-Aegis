"use client";

import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { getStoredUserId } from "@/lib/localAuth";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [userId, setUserId] = useState<string | null | undefined>(undefined);
  const previewMode = process.env.NEXT_PUBLIC_AUTH_PREVIEW_MODE === "true";

  useEffect(() => {
    if (previewMode) {
      setUserId("preview-user");
      return;
    }

    const storedUserId = getStoredUserId();
    setUserId(storedUserId);
    if (!storedUserId && pathname !== "/login") router.replace("/login");
  }, [pathname, previewMode, router]);

  if (previewMode) {
    return children;
  }

  if (userId === undefined) {
    return <div className="loading-screen">Loading Aegis...</div>;
  }

  if (!userId) {
    return null;
  }

  return children;
}
