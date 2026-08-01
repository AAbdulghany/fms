import { ReactNode, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";
import { hasFeature } from "@/lib/features";
import { FeatureUnavailablePage } from "@/features/shared/pages/FeatureUnavailablePage";

interface FeatureRouteProps {
  feature: string;
  children: ReactNode;
}

/** Gates child routes when the user's subscription lacks a feature module. */
export function FeatureRoute({ feature, children }: FeatureRouteProps) {
  const [user, setUser] = useState<User | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const data = await apiFetch<User>("/users/me");
        setUser(data);
      } catch {
        // ProtectedRoute already guards auth
      } finally {
        setChecked(true);
      }
    })();
  }, []);

  if (!checked) return null;

  if (user && !hasFeature(user, feature)) {
    return <FeatureUnavailablePage feature={feature} />;
  }

  return <>{children}</>;
}
