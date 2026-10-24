/**
 * A1 — Hook to load the tenant's asset type library.
 * Also exports `localizedName` as a pure helper for consistent display.
 */
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiFetch } from "@/lib/api";
import type { AssetType } from "@/lib/types";

/** Return the display name for a type in the current locale. */
export function localizedName(
  type: { name_en: string; name_ar: string },
  lang: string
): string {
  return lang.startsWith("ar") ? type.name_ar : type.name_en;
}

interface UseAssetTypesResult {
  types: AssetType[];
  loading: boolean;
  error: string | null;
  reload: () => void;
  lang: string;
}

/**
 * Load `/asset-types`.  When `clientId` is provided the server marks
 * types recommended for that client's vertical and sorts them first.
 * Pass `matchVertical` to exclude types not tagged for the client vertical.
 */
export function useAssetTypes(
  clientId?: string,
  options?: { matchVertical?: boolean }
): UseAssetTypesResult {
  const { i18n } = useTranslation();
  const [types, setTypes] = useState<AssetType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const matchVertical = options?.matchVertical ?? false;

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    const qs = new URLSearchParams();
    if (clientId) qs.set("client_id", clientId);
    if (matchVertical) qs.set("match_vertical", "true");
    const url = qs.toString() ? `/asset-types?${qs}` : "/asset-types";
    void apiFetch<AssetType[]>(url)
      .then((data) => setTypes(data))
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Failed to load asset types")
      )
      .finally(() => setLoading(false));
  }, [clientId, matchVertical]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { types, loading, error, reload, lang: i18n.language };
}
