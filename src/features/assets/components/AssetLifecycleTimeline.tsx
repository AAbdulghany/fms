import { useTranslation } from "react-i18next";
import { Asset, AssetLifecycleEvent } from "@/lib/types";

interface AssetLifecycleTimelineProps {
  asset: Asset;
  events?: AssetLifecycleEvent[];
}

function formatDate(dateStr: string, locale: string): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function AssetLifecycleTimeline({ asset, events: _events = [] }: AssetLifecycleTimelineProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const isRTL = i18n.dir() === "rtl";

  const currentAge = asset.age_years;
  const expectedLifespan = asset.expected_lifespan_years;
  const percentComplete = Math.min((currentAge / (expectedLifespan || 1)) * 100, 100);

  const barColor =
    asset.lifecycle_status === "end_of_life"
      ? "bg-error-main"
      : asset.lifecycle_status === "warning"
      ? "bg-warning-main"
      : "bg-success-main";

  const nowDotColor =
    asset.lifecycle_status === "end_of_life"
      ? "bg-error-main"
      : asset.lifecycle_status === "warning"
      ? "bg-warning-main"
      : "bg-primary-600";

  const eolInstallDate = asset.installation_date
    ? new Date(
        new Date(asset.installation_date).getTime() +
          expectedLifespan * 365.25 * 24 * 3600 * 1000
      ).toLocaleDateString(locale, { year: "numeric", month: "short" })
    : `${expectedLifespan} ${t("years")}`;

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0 p-6" dir={isRTL ? "rtl" : "ltr"}>
      <h3 className="mb-6 text-base font-semibold text-neutral-900">
        {t("asset_lifecycle_timeline")}
      </h3>

      <div>
        <div className="relative">
          <div className="relative mx-4 h-2 rounded-full bg-neutral-200 sm:mx-8">
            {/* Active portion */}
            <div
              className={`absolute inset-y-0 rounded-full ${barColor} transition-all duration-500`}
              style={{ [isRTL ? "right" : "left"]: 0, width: `${percentComplete}%` }}
            />

            {/* Installation dot */}
            <div
              className="absolute top-1/2 -translate-y-1/2 z-10"
              style={{ [isRTL ? "right" : "left"]: 0, transform: "translateX(-50%) translateY(-50%)" }}
            >
              <div className="h-4 w-4 rounded-full bg-primary-500 ring-2 ring-neutral-0 shadow-sm" />
            </div>

            {/* NOW dot */}
            {percentComplete < 100 && (
              <div
                className="absolute top-1/2 z-10"
                style={{
                  [isRTL ? "right" : "left"]: `${percentComplete}%`,
                  transform: "translateX(-50%) translateY(-50%)",
                }}
              >
                <div className={`h-4 w-4 animate-pulse rounded-full ${nowDotColor} ring-2 ring-neutral-0 shadow-sm`} />
              </div>
            )}

            {/* EOL dot */}
            <div
              className="absolute top-1/2 z-10"
              style={{ [isRTL ? "left" : "right"]: 0, transform: "translateX(50%) translateY(-50%)" }}
            >
              <div
                className={`h-4 w-4 rounded-full ring-2 ring-neutral-0 shadow-sm ${
                  percentComplete >= 100 ? "bg-error-main" : "bg-neutral-300"
                }`}
              />
            </div>
          </div>

          <div className="mt-4 flex items-start justify-between gap-6">
            <div className="min-w-0 max-w-[46%] text-start">
              <p className="text-xs font-semibold text-neutral-700">{t("timeline_installed")}</p>
              <p className="mt-0.5 text-xs text-neutral-500">
                {formatDate(asset.installation_date, locale)}
              </p>
            </div>
            <div className="min-w-0 max-w-[46%] text-end">
              <p className="text-xs font-semibold text-neutral-700">{t("timeline_eol")}</p>
              <p className="mt-0.5 text-xs text-neutral-500">{eolInstallDate}</p>
            </div>
          </div>
        </div>

        <p className="mt-4 text-sm font-semibold text-neutral-900">
          {percentComplete.toFixed(1)}% {t("lifespan_used")}
        </p>
      </div>
    </div>
  );
}
