import type { CSSProperties } from "react";
import { QRCodeSVG } from "qrcode.react";

type Design = "a" | "c";

type Props = {
  design: Design;
  deepLink: string;
  companyName?: string | null;
  assetName: string;
  labelCode?: string | null;
  serial?: string | null;
};

const NAVY = "#123056";
const COPPER = "#e85d04";
const INK = "#0f172a";
const MUTED = "#5b6b7c";

const ARABIC_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/;
const STICKER_FONT =
  '"Noto Sans Arabic", "IBM Plex Sans Arabic", "Segoe UI", system-ui, sans-serif';

function hasArabic(text: string): boolean {
  return ARABIC_RE.test(text);
}

function stickerTextStyle(extra?: CSSProperties): CSSProperties {
  return {
    fontFamily: STICKER_FONT,
    // Let the browser shape Arabic; do not pre-bidi (that caused reversed glyphs in PDF viewers).
    ...extra,
  };
}

/** Inline periapsis mark (vector) for QR center eye. */
function PeriapsisMark({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 256 256" aria-hidden>
      <path
        fill={NAVY}
        d="M 131.59 25.06 A 103 103 0 1 0 222.1 86.11 L 191.03 99.94 A 69 69 0 1 1 130.41 59.04 Z"
      />
      <path fill={NAVY} d="M 114 42.05 A 17 17 0 1 0 148 42.05 A 17 17 0 1 0 114 42.05 Z" />
      <path fill={NAVY} d="M 189.56 93.02 A 17 17 0 1 0 223.56 93.02 A 17 17 0 1 0 189.56 93.02 Z" />
      <path
        fill={COPPER}
        d="M 167.09 31.7 L 185.09 31.7 A 14 14 0 0 1 199.09 45.7 L 199.09 63.7 A 14 14 0 0 1 185.09 77.7 L 167.09 77.7 A 14 14 0 0 1 153.09 63.7 L 153.09 45.7 A 14 14 0 0 1 167.09 31.7 Z"
      />
    </svg>
  );
}

function QrWithMark({ value, size }: { value: string; size: number }) {
  const eye = Math.round(size * 0.22);
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <QRCodeSVG value={value} size={size} level="H" fgColor={NAVY} bgColor="#ffffff" includeMargin={false} />
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[18%] bg-white"
        style={{ width: eye * 1.2, height: eye * 1.2 }}
      >
        <PeriapsisMark size={eye} />
      </div>
    </div>
  );
}

export function AssetStickerPreview({
  design,
  deepLink,
  companyName,
  assetName,
  labelCode,
  serial,
}: Props) {
  const company = (companyName || "—").trim();
  const id = (labelCode || "—").trim();
  const sn = (serial || "—").trim();

  if (design === "c") {
    // Layout mirrors PDF Design C: copper spine · QR · stacked copy (no hang hole)
    return (
      <div
        className="relative mx-auto w-full max-w-[340px] overflow-hidden rounded-[14px] border-[3.5px] bg-white"
        style={{ borderColor: NAVY, aspectRatio: "60 / 35" }}
        data-testid="asset-sticker-preview"
      >
        <div className="absolute inset-y-0 left-0 w-[3.5%]" style={{ background: COPPER }} />
        <div className="flex h-full items-center gap-3 py-2.5 pl-[7%] pr-[5%]">
          <QrWithMark value={deepLink} size={112} />
          <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
            <p
              className={`truncate text-[9px] font-bold leading-snug tracking-wide ${
                hasArabic(company) ? "" : "uppercase"
              }`}
              style={stickerTextStyle({ color: COPPER })}
              dir="auto"
            >
              {company}
            </p>
            <p
              className="line-clamp-2 text-[13px] font-bold leading-snug"
              style={stickerTextStyle({ color: NAVY })}
              dir="auto"
            >
              {assetName}
            </p>
            <div className="mt-1.5 flex flex-col gap-1">
              <p className="truncate text-[10px] leading-normal" style={stickerTextStyle({ color: MUTED })} dir="auto">
                ID {id}
              </p>
              <p className="truncate text-[10px] leading-normal" style={stickerTextStyle({ color: MUTED })} dir="auto">
                SN {sn}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const companyUpper = !hasArabic(company);
  const qrSize = 156;

  return (
    <div
      className="relative mx-auto aspect-square w-full max-w-[280px] overflow-hidden rounded-[18px] border-[4.5px] bg-white p-3"
      style={{ borderColor: NAVY }}
      data-testid="asset-sticker-preview"
    >
      <div
        className="absolute right-0 top-0 h-5 w-5"
        style={{ background: COPPER, clipPath: "polygon(0 0, 100% 0, 100% 100%)" }}
      />
      <p
        className={`truncate text-center text-[10px] font-bold tracking-wide ${
          companyUpper ? "uppercase" : ""
        }`}
        style={stickerTextStyle({ color: NAVY })}
        dir="auto"
      >
        {company}
      </p>
      <div className="mt-1.5 flex justify-center">
        <QrWithMark value={deepLink} size={qrSize} />
      </div>
      <p
        className="mt-1.5 line-clamp-2 text-center text-[12px] font-semibold leading-tight"
        style={stickerTextStyle({ color: INK })}
        dir="auto"
      >
        {assetName}
      </p>
      <p className="mt-1 truncate text-center text-[10px]" style={stickerTextStyle({ color: MUTED })} dir="auto">
        ID {id}
      </p>
      <p className="truncate text-center text-[10px]" style={stickerTextStyle({ color: MUTED })} dir="auto">
        SN {sn}
      </p>
    </div>
  );
}
