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
    return (
      <div
        className="relative mx-auto w-full max-w-[340px] overflow-hidden rounded-[14px] border-[3.5px] bg-white"
        style={{ borderColor: NAVY, aspectRatio: "60 / 35" }}
        data-testid="asset-sticker-preview"
      >
        <div className="absolute inset-y-0 left-0 w-[3.5%]" style={{ background: COPPER }} />
        <div
          className="absolute right-[6%] top-1/2 h-[16%] w-[9%] -translate-y-1/2 rounded-full border-2 bg-[#f7f9fc]"
          style={{ borderColor: NAVY }}
        />
        <div className="flex h-full items-center gap-2 py-2 pl-[7%] pr-[14%]">
          <QrWithMark value={deepLink} size={112} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-[9px] font-bold uppercase tracking-wide" style={{ color: COPPER }}>
              {company}
            </p>
            <p className="mt-0.5 line-clamp-2 text-[13px] font-bold leading-tight" style={{ color: NAVY }}>
              {assetName}
            </p>
            <p className="mt-1.5 truncate text-[10px]" style={{ color: MUTED }}>
              ID {id}
            </p>
            <p className="truncate text-[10px]" style={{ color: MUTED }}>
              SN {sn}
            </p>
          </div>
        </div>
      </div>
    );
  }

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
        className="truncate text-center text-[10px] font-bold uppercase tracking-wide"
        style={{ color: NAVY }}
      >
        {company}
      </p>
      <div className="mt-2 flex justify-center">
        <QrWithMark value={deepLink} size={168} />
      </div>
      <p className="mt-2 truncate text-center text-[13px] font-semibold" style={{ color: INK }}>
        {assetName}
      </p>
      <p className="mt-0.5 truncate text-center text-[10px]" style={{ color: MUTED }}>
        ID {id} · SN {sn}
      </p>
    </div>
  );
}
