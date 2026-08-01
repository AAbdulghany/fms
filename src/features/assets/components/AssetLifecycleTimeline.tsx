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

      {/* Desktop: Horizontal Timeline */}
      <div className="hidden sm:block">
        <div className="relative">
          {/* Progress bar track */}
          <div className="relative mx-8 h-2 rounded-full bg-neutral-200">
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

          {/* Labels row */}
          <div className="relative mt-4 flex justify-between text-center">
            <div className="w-24">
              <p className="text-xs font-semibold text-neutral-700">{t("timeline_installed")}</p>
              <p className="mt-0.5 text-xs text-neutral-500">
                {formatDate(asset.installation_date, locale)}
              </p>
            </div>

            {percentComplete > 10 && percentComplete < 90 && (
              <div
                className="absolute flex flex-col items-center"
                style={{ [isRTL ? "right" : "left"]: `${percentComplete}%`, transform: "translateX(-50%)" }}
              >
                <p className={`text-xs font-bold ${nowDotColor.replace("bg-", "text-")}`}>
                  {t("timeline_now")}
                </p>
                <p className="text-xs text-neutral-500">
                  {currentAge.toFixed(1)} {t("years")}
                </p>
              </div>
            )}

            <div className="w-24">
              <p className="text-xs font-semibold text-neutral-700">{t("timeline_eol")}</p>
              <p className="mt-0.5 text-xs text-neutral-500">{eolInstallDate}</p>
            </div>
          </div>
        </div>

        {/* Status bar */}
        <div className="mt-6 rounded-md border border-neutral-100 bg-neutral-50 px-4 py-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-600">{t("lifespan_used")}</span>
            <span className="font-semibold text-neutral-900">
              {Math.round(percentComplete)}%
            </span>
          </div>
          <div className="mt-2 h-1.5 w-full rounded-full bg-neutral-200">
            <div
              className={`h-full rounded-full ${barColor}`}
              style={{ width: `${percentComplete}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-neutral-500">
            {asset.lifecycle_status === "warning" &&
              t("timeline_warning_hint", {
                pct: Math.round(percentComplete),
                defaultValue: `Asset is ${Math.round(percentComplete)}% through expected lifespan`,
              })}
            {asset.lifecycle_status === "end_of_life" && t("timeline_eol_hint")}
            {asset.lifecycle_status === "active" && t("timeline_active_hint")}
          </p>
        </div>
      </div>

      {/* Mobile: Vertical Timeline */}
      <div className="sm:hidden">
        <ol className="relative border-s border-neutral-200" style={{ borderInlineStart: "2px solid", borderColor: "var(--color-neutral-200)" }}>
          <li className="mb-6 ms-6">
            <span className="absolute -start-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-primary-500 ring-2 ring-neutral-0" />
            <p className="text-sm font-semibold text-neutral-900">{t("timeline_installed")}</p>
            <p className="text-xs text-neutral-500">{formatDate(asset.installation_date, locale)}</p>
          </li>
          <li className="mb-6 ms-6">
            <span className={`absolute -start-[9px] flex h-4 w-4 animate-pulse items-center justify-center rounded-full ${nowDotColor} ring-2 ring-neutral-0`} />
            <p className={`text-sm font-semibold ${nowDotColor.replace("bg-", "text-")}`}>{t("timeline_now")}</p>
            <p className="text-xs text-neutral-500">
              {currentAge.toFixed(1)} {t("years")} · {Math.round(percentComplete)}% {t("lifespan_used")}
            </p>
          </li>
          <li className="ms-6">
            <span
              className={`absolute -start-[9px] flex h-4 w-4 items-center justify-center rounded-full ring-2 ring-neutral-0 ${
                percentComplete >= 100 ? "bg-error-main" : "bg-neutral-300"
              }`}
            />
            <p className="text-sm font-semibold text-neutral-900">{t("timeline_eol")}</p>
            <p className="text-xs text-neutral-500">{eolInstallDate}</p>
          </li>
        </ol>
      </div>
    </div>
  );
}
