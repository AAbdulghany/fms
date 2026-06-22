import { useTranslation } from "react-i18next";

interface OrbitLogoProps {
  /** Show the wordmark beside the mark */
  showWordmark?: boolean;
  /** Icon size in pixels */
  iconSize?: number;
  className?: string;
}

/** Orbit brand mark — orbital ring around a core node (facility hub metaphor). */
export function OrbitLogo({
  showWordmark = true,
  iconSize = 28,
  className = "",
}: OrbitLogoProps) {
  const { t } = useTranslation();

  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-hidden={showWordmark ? true : undefined}
        aria-label={showWordmark ? undefined : "Orbit"}
      >
        <circle cx="16" cy="16" r="4.5" className="fill-primary-600" />
        <ellipse
          cx="16"
          cy="16"
          rx="11.5"
          ry="5"
          className="stroke-primary-600"
          strokeWidth="2"
          transform="rotate(-22 16 16)"
        />
        <ellipse
          cx="16"
          cy="16"
          rx="11.5"
          ry="5"
          className="stroke-primary-400"
          strokeWidth="1.5"
          strokeOpacity="0.45"
          transform="rotate(38 16 16)"
        />
      </svg>
      {showWordmark && (
        <span className="font-display-ar text-lg font-semibold tracking-tight text-primary-600 lg:text-xl">
          {t("app_title")}
        </span>
      )}
    </span>
  );
}
