/**
 * A1 — Returns the localized display name for an asset row.
 * Prefers asset_type.name_* when the type is linked, and falls back to the
 * raw category string (legacy behaviour).
 */
export function assetTypeLabel(
  row: {
    asset_type?: { name_en: string; name_ar: string } | null;
    category?: string;
  },
  lang: string
): string {
  const isAr = lang.startsWith("ar");
  if (row.asset_type) {
    return isAr ? row.asset_type.name_ar : row.asset_type.name_en;
  }
  return row.category ?? "";
}
