import { useTranslation } from "react-i18next";

interface OrbitLogoProps {
  /** Show the wordmark beside the mark */
  showWordmark?: boolean;
  /** Icon size in pixels */
  iconSize?: number;
  /** Light mark for the navy login panel */
  tone?: "default" | "onDark";
  className?: string;
}

/** Periapsis mark — open orbit with the asset seated in the gap. */
const RING =
  "M 131.59 25.06 A 103 103 0 1 0 222.1 86.11 L 191.03 99.94 A 69 69 0 1 1 130.41 59.04 Z";
const CAP_A = "M 114 42.05 A 17 17 0 1 0 148 42.05 A 17 17 0 1 0 114 42.05 Z";
const CAP_B = "M 189.56 93.02 A 17 17 0 1 0 223.56 93.02 A 17 17 0 1 0 189.56 93.02 Z";
const ASSET =
  "M 167.09 31.7 L 185.09 31.7 A 14 14 0 0 1 199.09 45.7 L 199.09 63.7 A 14 14 0 0 1 185.09 77.7 L 167.09 77.7 A 14 14 0 0 1 153.09 63.7 L 153.09 45.7 A 14 14 0 0 1 167.09 31.7 Z";
export function OrbitLogo({
  showWordmark = true,
  iconSize = 28,
  tone = "default",
  className = "",
}: OrbitLogoProps) {
  const { t } = useTranslation();

  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 256 256"
        className={tone === "onDark" ? "text-neutral-50" : "text-primary-700"}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-hidden={showWordmark ? true : undefined}
        aria-label={showWordmark ? undefined : "Orbit"}
      >
        <path className="fill-current" d={RING} />
        <path className="fill-current" d={CAP_A} />
        <path className="fill-current" d={CAP_B} />
        <path className="fill-secondary-500" d={ASSET} />
      </svg>
      {showWordmark && (
        <span className="font-display-ar text-lg font-semibold tracking-tight text-primary-600 lg:text-xl">
          {t("app_title")}
        </span>
      )}
    </span>
  );
}
