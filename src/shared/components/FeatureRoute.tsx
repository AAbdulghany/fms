import { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { hasFeature } from "@/lib/features";
import { FeatureUnavailablePage } from "@/features/shared/pages/FeatureUnavailablePage";

interface FeatureRouteProps {
  feature: string;
  children: ReactNode;
}

/** Gates child routes when the user's subscription lacks a feature module. */
export function FeatureRoute({ feature, children }: FeatureRouteProps) {
  const { user, loading } = useAuth();

  if (loading) return null;

  if (user && !hasFeature(user, feature)) {
    return <FeatureUnavailablePage feature={feature} />;
  }

  return <>{children}</>;
}
