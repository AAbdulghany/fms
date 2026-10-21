/**
 * A1 — Asset Type Picker.
 *
 * A native <select> that groups types into "Recommended" and "All types".
 * When the tenant library is empty, it renders an empty-state hint and
 * (for admins) a link to the asset-type library.  A free-text fallback
 * is provided so registration is never blocked pre-backfill.
 */
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { AssetType, UserRole } from "@/lib/types";
import { localizedName } from "@/features/assets/hooks/useAssetTypes";

interface AssetTypePickerProps {
  types: AssetType[];
  value: string;
  onChange: (typeId: string) => void;
  loading?: boolean;
  error?: string | null;
  userRole?: UserRole;
  /** Shown as the "Recommended for …" group label when vertical is known */
  verticalLabel?: string;
  /** Free-text fallback when library is empty */
  freeTextCategory?: string;
  onFreeTextChange?: (v: string) => void;
  required?: boolean;
}

export function AssetTypePicker({
  types,
  value,
  onChange,
  loading,
  error,
  userRole,
  verticalLabel,
  freeTextCategory,
  onFreeTextChange,
  required,
}: AssetTypePickerProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;

  const isAdmin =
    userRole === "company_admin" || userRole === "super_admin" || userRole === "super_user";

  const recommended = types.filter((ty) => ty.recommended);
  const rest = types.filter((ty) => !ty.recommended);

  // ── Empty library ─────────────────────────────────────────────────────────
  if (!loading && types.length === 0) {
    return (
      <div className="space-y-2">
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-sm text-neutral-600">
          <p>{t("no_asset_types_user")}</p>
          {isAdmin && (
            <Link
              to="/asset-types"
              className="mt-1 inline-block text-primary-600 underline hover:text-primary-700"
            >
              {t("no_asset_types_admin")}
            </Link>
          )}
        </div>
        {/* Free-text fallback so registration is never blocked */}
        {onFreeTextChange && (
          <div>
            <label className="mb-1 block text-xs text-neutral-500">{t("category")}</label>
            <input
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              value={freeTextCategory ?? ""}
              onChange={(e) => onFreeTextChange(e.target.value)}
              placeholder={t("asset_category_placeholder")}
            />
          </div>
        )}
      </div>
    );
  }

  // ── Normal picker ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-1">
      <select
        required={required && types.length > 0}
        disabled={loading}
        className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-100"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={t("select_asset_type")}
      >
        <option value="">{loading ? t("loading") : t("select_asset_type")}</option>

        {/* Recommended group */}
        {recommended.length > 0 && (
          <optgroup
            label={
              verticalLabel
                ? `${t("recommended_for_vertical")} ${verticalLabel}`
                : t("recommended_for_vertical")
            }
          >
            {recommended.map((ty) => (
              <option key={ty.id} value={ty.id}>
                {localizedName(ty, lang)}
              </option>
            ))}
          </optgroup>
        )}

        {/* All types */}
        {rest.length > 0 && (
          <optgroup label={t("all_asset_types")}>
            {rest.map((ty) => (
              <option key={ty.id} value={ty.id}>
                {localizedName(ty, lang)}
              </option>
            ))}
          </optgroup>
        )}
      </select>

      {error && (
        <p className="text-xs text-error-main">{error}</p>
      )}
    </div>
  );
}
