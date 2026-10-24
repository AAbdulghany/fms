import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getAccessToken } from "@/lib/api";
import { AssetStickerPreview } from "@/features/assets/components/AssetStickerPreview";

type Props = {
  open: boolean;
  assetId: string;
  assetName: string;
  companyName?: string | null;
  labelCode?: string | null;
  serial?: string | null;
  qrPayload?: string | null;
  onClose: () => void;
};

type StickerDesign = "a" | "c";

const SIZE_PRESETS_A = [50, 70, 90] as const;
const SIZE_PRESETS_C = [60, 80, 100] as const;

function resolveDeepLink(assetId: string, qrPayload?: string | null): string {
  if (qrPayload) {
    if (qrPayload.startsWith("http://") || qrPayload.startsWith("https://")) {
      return qrPayload;
    }
    if (qrPayload.includes("/a/")) {
      return `${window.location.origin}${qrPayload.startsWith("/") ? "" : "/"}${qrPayload}`;
    }
  }
  return `${window.location.origin}/assets/${assetId}`;
}

export function AssetQrModal({
  open,
  assetId,
  assetName,
  companyName,
  labelCode,
  serial,
  qrPayload,
  onClose,
}: Props) {
  const { t } = useTranslation();
  const [design, setDesign] = useState<StickerDesign>("a");
  const [sizeMm, setSizeMm] = useState<number>(70);
  const [printing, setPrinting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewFailed, setPreviewFailed] = useState(false);

  useEffect(() => {
    setSizeMm(design === "c" ? 80 : 70);
  }, [design]);

  // WYSIWYG: preview is a PNG of the exact print PDF (same renderer as طباعة الملصق)
  useEffect(() => {
    if (!open) {
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }

    let cancelled = false;
    let objectUrl: string | null = null;
    const ctrl = new AbortController();

    async function loadPreview() {
      setPreviewLoading(true);
      setPreviewFailed(false);
      try {
        const token = getAccessToken();
        const qs = new URLSearchParams({
          size_mm: String(sizeMm),
          design,
          format: "png",
          t: String(Date.now()),
        });
        const res = await fetch(`/api/v1/assets/${assetId}/label-sheet?${qs}`, {
          cache: "no-store",
          signal: ctrl.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error(`preview ${res.status}`);
        const blob = await res.blob();
        objectUrl = URL.createObjectURL(blob);
        if (cancelled) {
          URL.revokeObjectURL(objectUrl);
          return;
        }
        setPreviewUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return objectUrl;
        });
      } catch (err) {
        if (cancelled || (err instanceof DOMException && err.name === "AbortError")) return;
        setPreviewFailed(true);
        setPreviewUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return null;
        });
      } finally {
        if (!cancelled) setPreviewLoading(false);
      }
    }

    void loadPreview();
    return () => {
      cancelled = true;
      ctrl.abort();
    };
  }, [open, assetId, design, sizeMm]);

  if (!open) return null;

  const deepLink = resolveDeepLink(assetId, qrPayload);
  const presets = design === "c" ? SIZE_PRESETS_C : SIZE_PRESETS_A;
  const sizeHint = design === "c" ? t("sticker_size_hint_c") : t("sticker_size_hint");

  async function printLabel() {
    setPrinting(true);
    try {
      const token = getAccessToken();
      const qs = new URLSearchParams({
        size_mm: String(sizeMm),
        design,
        format: "pdf",
        t: String(Date.now()),
      });
      const res = await fetch(`/api/v1/assets/${assetId}/label-sheet?${qs}`, {
        cache: "no-store",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } finally {
      setPrinting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        className="max-h-[92vh] w-full max-w-md overflow-y-auto rounded-xl bg-neutral-0 p-6 shadow-xl"
        role="dialog"
        aria-modal
        data-testid="asset-qr-modal"
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-neutral-900">{t("qr_sticker_preview")}</h2>
            <p className="mt-0.5 text-sm text-neutral-600">{assetName}</p>
          </div>
          <button
            type="button"
            className="rounded-md p-1 text-neutral-400 hover:text-neutral-600"
            onClick={onClose}
            aria-label={t("close")}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt={t("qr_sticker_preview")}
              className={`mx-auto w-full bg-white ${
                design === "c" ? "max-w-[340px]" : "max-w-[280px]"
              }`}
              data-testid="asset-sticker-preview-print"
            />
          ) : previewLoading ? (
            <div
              className={`mx-auto flex items-center justify-center bg-white text-sm text-neutral-500 ${
                design === "c" ? "aspect-[60/35] max-w-[340px]" : "aspect-square max-w-[280px]"
              }`}
              data-testid="asset-sticker-preview-loading"
            >
              {t("loading")}
            </div>
          ) : (
            // Fallback approximation only if PNG preview fails
            <AssetStickerPreview
              design={design}
              deepLink={deepLink}
              companyName={companyName}
              assetName={assetName}
              labelCode={labelCode}
              serial={serial}
            />
          )}
          {previewFailed ? (
            <p className="mt-2 text-center text-xs text-amber-700">
              {t("sticker_preview_fallback") || "Showing approximate preview — print uses the exact label."}
            </p>
          ) : null}
        </div>

        <p
          className="mt-3 break-all text-center text-xs text-neutral-500"
          data-testid="asset-qr-link"
        >
          {deepLink}
        </p>

        <div className="mt-4">
          <p className="mb-1.5 text-sm font-medium text-neutral-700">{t("sticker_design")}</p>
          <div className="flex flex-wrap gap-2" data-testid="asset-qr-design">
            <button
              type="button"
              className={`rounded-md border px-2.5 py-1 text-sm ${
                design === "a"
                  ? "border-primary-600 bg-primary-50 text-primary-800"
                  : "border-neutral-300 text-neutral-700 hover:bg-neutral-50"
              }`}
              onClick={() => setDesign("a")}
            >
              {t("sticker_design_a")}
            </button>
            <button
              type="button"
              className={`rounded-md border px-2.5 py-1 text-sm ${
                design === "c"
                  ? "border-primary-600 bg-primary-50 text-primary-800"
                  : "border-neutral-300 text-neutral-700 hover:bg-neutral-50"
              }`}
              onClick={() => setDesign("c")}
            >
              {t("sticker_design_c")}
            </button>
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1.5 block text-sm font-medium text-neutral-700" htmlFor="sticker-size">
            {t("sticker_size_mm")}
          </label>
          <div className="flex flex-wrap items-center gap-2">
            {presets.map((preset) => (
              <button
                key={preset}
                type="button"
                className={`rounded-md border px-2.5 py-1 text-sm ${
                  sizeMm === preset
                    ? "border-primary-600 bg-primary-50 text-primary-800"
                    : "border-neutral-300 text-neutral-700 hover:bg-neutral-50"
                }`}
                onClick={() => setSizeMm(preset)}
              >
                {preset} mm
              </button>
            ))}
            <input
              id="sticker-size"
              type="number"
              min={40}
              max={120}
              step={1}
              value={sizeMm}
              data-testid="asset-qr-size-mm"
              onChange={(e) => {
                const n = Number(e.target.value);
                if (Number.isFinite(n)) setSizeMm(Math.min(120, Math.max(40, Math.round(n))));
              }}
              className="w-20 rounded-md border border-neutral-300 px-2 py-1 text-sm"
            />
          </div>
          <p className="mt-1 text-xs text-neutral-500">{sizeHint}</p>
        </div>

        <div className="mt-4 flex flex-wrap justify-end gap-2">
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50"
            onClick={() => {
              void navigator.clipboard.writeText(deepLink);
            }}
          >
            {t("copy_link")}
          </button>
          <button
            type="button"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50 disabled:opacity-60"
            disabled={printing}
            onClick={() => {
              void printLabel();
            }}
          >
            {printing ? t("loading") : t("print_label")}
          </button>
          <button
            type="button"
            data-testid="asset-qr-close"
            className="rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
            onClick={onClose}
          >
            {t("close")}
          </button>
        </div>
      </div>
    </div>
  );
}
