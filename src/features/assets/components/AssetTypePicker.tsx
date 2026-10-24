/**
 * Asset type field — type a name (creates if new) or pick an existing one.
 */
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { AssetType, UserRole } from "@/lib/types";
import { localizedName } from "@/features/assets/hooks/useAssetTypes";

interface AssetTypePickerProps {
  types: AssetType[];
  /** Selected existing type id (optional when using free text) */
  value: string;
  onChange: (typeId: string) => void;
  /** Free-text label sent as asset_type_name */
  typeName: string;
  onTypeNameChange: (name: string) => void;
  loading?: boolean;
  error?: string | null;
  userRole?: UserRole;
  required?: boolean;
}

export function AssetTypePicker({
  types,
  value,
  onChange,
  typeName,
  onTypeNameChange,
  loading,
  error,
  userRole,
  required,
}: AssetTypePickerProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [open, setOpen] = useState(false);

  const isAdmin =
    userRole === "company_admin" || userRole === "super_admin" || userRole === "super_user";

  const suggestions = useMemo(() => {
    const q = typeName.trim().toLowerCase();
    if (!q) return types.slice(0, 12);
    return types
      .filter(
        (ty) =>
          ty.name_en.toLowerCase().includes(q) ||
          ty.name_ar.toLowerCase().includes(q) ||
          ty.code.toLowerCase().includes(q)
      )
      .slice(0, 12);
  }, [types, typeName]);

  function pick(ty: AssetType) {
    onChange(ty.id);
    onTypeNameChange(localizedName(ty, lang));
    setOpen(false);
  }

  function onInput(v: string) {
    onTypeNameChange(v);
    // Typing a new name clears a previous id pick so find-or-create runs
    if (value) {
      const selected = types.find((t) => t.id === value);
      if (!selected || localizedName(selected, lang) !== v) {
        onChange("");
      }
    }
    setOpen(true);
  }

  return (
    <div className="space-y-1">
      <div className="relative">
        <input
          required={required}
          disabled={loading}
          list="asset-type-suggestions"
          data-testid="asset-type-picker"
          className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm disabled:bg-neutral-100"
          value={typeName}
          onChange={(e) => onInput(e.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder={t("asset_type_placeholder") || "e.g. Chiller, Elevator, Pump…"}
          aria-label={t("select_asset_type")}
          autoComplete="off"
        />
        <datalist id="asset-type-suggestions">
          {types.map((ty) => (
            <option key={ty.id} value={localizedName(ty, lang)} />
          ))}
        </datalist>
        {open && suggestions.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-md border border-neutral-200 bg-white py-1 shadow-lg">
            {suggestions.map((ty) => (
              <li key={ty.id}>
                <button
                  type="button"
                  className="w-full px-3 py-1.5 text-start text-sm hover:bg-primary-50"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => pick(ty)}
                >
                  {localizedName(ty, lang)}
                  <span className="ms-2 text-xs text-neutral-400">{ty.code}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-xs text-neutral-500">
        {t("asset_type_create_hint") ||
          "Type a name — if it doesn’t exist yet, it will be created for next time."}
      </p>
      {isAdmin && (
        <Link to="/asset-types" className="text-xs text-primary-600 underline hover:text-primary-700">
          {t("manage_asset_types") || "Manage asset types"}
        </Link>
      )}
      {error && <p className="text-xs text-error-main">{error}</p>}
    </div>
  );
}
