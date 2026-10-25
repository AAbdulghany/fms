import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Html5Qrcode, type Html5QrcodeResult } from "html5-qrcode";
import { apiFetch, getAccessToken } from "@/lib/api";

type AssetHit = {
  id: string;
  name: string;
  label_code?: string | null;
  site_name?: string | null;
};

type PublicTag = {
  token: string;
  asset_id?: string | null;
};

const SCANNER_REGION_ID = "orbit-qr-reader";
/** Matches pen F Scan viewfinder — square QR window, not a full-bleed camera page. */
const VIEWFINDER_PX = 240;
const QRBOX_PX = 180;

/** Extract Orbit asset deep-link targets from a QR payload string. */
export function parseAssetScanPayload(raw: string): { kind: "tag"; token: string } | { kind: "asset"; id: string } | null {
  const text = raw.trim();
  if (!text) return null;

  const tagMatch = text.match(/\/a\/([A-Za-z0-9_-]+)/i);
  if (tagMatch?.[1]) {
    return { kind: "tag", token: tagMatch[1].toUpperCase() };
  }

  const assetMatch = text.match(/\/assets\/([0-9a-f-]{36})/i);
  if (assetMatch?.[1]) {
    return { kind: "asset", id: assetMatch[1] };
  }

  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(text)) {
    return { kind: "asset", id: text };
  }

  if (/^[A-Za-z0-9_-]{6,32}$/.test(text) && !text.includes("/")) {
    return { kind: "tag", token: text.toUpperCase() };
  }

  return null;
}

export default function ScanAssetPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const handlingRef = useRef(false);
  const startingRef = useRef(false);
  const cameraSessionRef = useRef(0);
  const handleDecodedRef = useRef<(decoded: string) => Promise<void>>(async () => undefined);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [cameraBusy, setCameraBusy] = useState(false);
  const [code, setCode] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [hits, setHits] = useState<AssetHit[]>([]);

  const goToAsset = useCallback(
    (assetId: string) => {
      navigate(`/assets/${assetId}`);
    },
    [navigate],
  );

  const resolveTag = useCallback(
    async (token: string) => {
      const headers: HeadersInit = {};
      const access = getAccessToken();
      if (access) headers.Authorization = `Bearer ${access}`;
      const res = await fetch(`/api/v1/public/asset-tags/${encodeURIComponent(token)}`, { headers });
      if (!res.ok) throw new Error("tag");
      const data = (await res.json()) as PublicTag;
      if (data.asset_id) {
        goToAsset(data.asset_id);
        return;
      }
      navigate(`/a/${token}`);
    },
    [goToAsset, navigate],
  );

  const handleDecoded = useCallback(
    async (decoded: string) => {
      if (handlingRef.current) return;
      handlingRef.current = true;
      setLookupError(null);
      try {
        const parsed = parseAssetScanPayload(decoded);
        if (!parsed) {
          setLookupError(t("scan_unrecognized_qr"));
          return;
        }
        if (parsed.kind === "asset") {
          goToAsset(parsed.id);
          return;
        }
        await resolveTag(parsed.token);
      } catch {
        setLookupError(t("scan_asset_not_found"));
      } finally {
        handlingRef.current = false;
      }
    },
    [goToAsset, resolveTag, t],
  );

  handleDecodedRef.current = handleDecoded;

  const stopCamera = useCallback(async () => {
    const scanner = scannerRef.current;
    if (!scanner) return;
    try {
      if (scanner.isScanning) {
        await scanner.stop();
      }
    } catch {
      /* already stopped */
    }
    try {
      scanner.clear();
    } catch {
      /* region may already be gone */
    }
    scannerRef.current = null;
    setScanning(false);
  }, []);

  const startCamera = useCallback(async () => {
    if (startingRef.current || scannerRef.current?.isScanning) return;
    const session = cameraSessionRef.current;
    startingRef.current = true;
    setCameraBusy(true);
    setCameraError(null);

    await stopCamera();
    if (session !== cameraSessionRef.current) {
      startingRef.current = false;
      setCameraBusy(false);
      return;
    }

    const region = document.getElementById(SCANNER_REGION_ID);
    if (!region) {
      setCameraError(t("scan_camera_unavailable"));
      setCameraBusy(false);
      startingRef.current = false;
      return;
    }

    const scanner = new Html5Qrcode(SCANNER_REGION_ID, { verbose: false });
    scannerRef.current = scanner;

    const config = {
      fps: 8,
      qrbox: { width: QRBOX_PX, height: QRBOX_PX },
      aspectRatio: 1,
      disableFlip: false,
    };
    const onSuccess = (text: string, _result: Html5QrcodeResult) => {
      void handleDecodedRef.current(text);
    };
    const onFailure = () => {
      /* ignore frame miss */
    };

    const cameras = await Html5Qrcode.getCameras().catch(() => [] as { id: string; label: string }[]);
    if (session !== cameraSessionRef.current) {
      startingRef.current = false;
      setCameraBusy(false);
      return;
    }
    const backCamera =
      cameras.find((cam) => /back|rear|environment|خلف|ظهر/i.test(cam.label)) ?? cameras[cameras.length - 1];

    const attempts: Array<string | MediaTrackConstraints> = [];
    if (backCamera?.id) attempts.push(backCamera.id);
    attempts.push({ facingMode: { exact: "environment" } });
    attempts.push({ facingMode: "environment" });
    if (cameras[0]?.id && cameras[0].id !== backCamera?.id) attempts.push(cameras[0].id);
    attempts.push({ facingMode: "user" });

    let started = false;
    let lastError: unknown = null;
    for (const cameraIdOrConfig of attempts) {
      if (session !== cameraSessionRef.current) break;
      try {
        await scanner.start(cameraIdOrConfig, config, onSuccess, onFailure);
        started = true;
        break;
      } catch (err) {
        lastError = err;
        try {
          if (scanner.isScanning) await scanner.stop();
        } catch {
          /* continue */
        }
      }
    }

    if (session !== cameraSessionRef.current) {
      try {
        if (scanner.isScanning) await scanner.stop();
        scanner.clear();
      } catch {
        /* ignore */
      }
      if (scannerRef.current === scanner) scannerRef.current = null;
      startingRef.current = false;
      setCameraBusy(false);
      return;
    }

    if (started) {
      setScanning(true);
      setCameraError(null);
    } else {
      console.warn("Orbit scan camera failed", lastError);
      setScanning(false);
      setCameraError(t("scan_camera_unavailable"));
      try {
        scanner.clear();
      } catch {
        /* ignore */
      }
      scannerRef.current = null;
    }

    setCameraBusy(false);
    startingRef.current = false;
  }, [stopCamera, t]);

  useEffect(() => {
    const session = ++cameraSessionRef.current;
    const timer = window.setTimeout(() => {
      if (session === cameraSessionRef.current) void startCamera();
    }, 50);
    return () => {
      window.clearTimeout(timer);
      cameraSessionRef.current += 1;
      void stopCamera();
    };
  }, [startCamera, stopCamera]);

  async function onSubmitCode(e: FormEvent) {
    e.preventDefault();
    const q = code.trim();
    if (!q || lookupBusy) return;
    setLookupBusy(true);
    setLookupError(null);
    setHits([]);
    try {
      const parsed = parseAssetScanPayload(q);
      if (parsed?.kind === "asset") {
        goToAsset(parsed.id);
        return;
      }
      if (parsed?.kind === "tag") {
        await resolveTag(parsed.token);
        return;
      }
      const results = await apiFetch<AssetHit[]>(`/assets?search=${encodeURIComponent(q)}`);
      if (results.length === 1) {
        goToAsset(results[0].id);
        return;
      }
      if (results.length === 0) {
        setLookupError(t("scan_asset_not_found"));
        return;
      }
      setHits(results.slice(0, 5));
    } catch {
      setLookupError(t("scan_asset_not_found"));
    } finally {
      setLookupBusy(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-3">
      <header className="min-w-0">
        <h1 className="text-lg font-bold tracking-tight text-neutral-900">{t("scan_asset_title")}</h1>
        <p className="mt-0.5 text-xs text-neutral-500">{t("scan_point_qr")}</p>
      </header>

      {/* Fixed square — stops html5-qrcode from expanding into a second full screen */}
      <div className="mx-auto w-full max-w-[240px]">
        <div
          className="relative overflow-hidden rounded-xl bg-neutral-900 shadow-sm"
          style={{ width: "100%", height: VIEWFINDER_PX }}
        >
          <div
            id={SCANNER_REGION_ID}
            className="orbit-qr-viewfinder absolute inset-0 overflow-hidden"
          />
          {!scanning && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-neutral-900/95 px-4 text-center">
              {cameraError && <p className="text-xs text-neutral-200">{cameraError}</p>}
              <button
                type="button"
                onClick={() => {
                  void startCamera();
                }}
                disabled={cameraBusy}
                className="min-h-11 rounded-xl bg-secondary-500 px-5 text-sm font-bold text-neutral-900 disabled:opacity-60"
              >
                {cameraBusy ? t("scan_opening_camera") : t("scan_open_camera")}
              </button>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={onSubmitCode} className="flex flex-col gap-1.5">
        <label htmlFor="asset-code" className="text-xs font-semibold text-neutral-600">
          {t("scan_enter_code")}
        </label>
        <div className="flex gap-2">
          <input
            id="asset-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={t("scan_code_placeholder")}
            className="min-h-10 flex-1 rounded-lg border border-neutral-300 bg-neutral-0 px-3 text-sm"
            autoComplete="off"
          />
          <button
            type="submit"
            disabled={lookupBusy || !code.trim()}
            className="min-h-10 shrink-0 rounded-lg bg-primary-700 px-3 text-sm font-semibold text-white hover:bg-primary-800 disabled:opacity-50"
          >
            {t("scan_open_asset")}
          </button>
        </div>
      </form>

      {lookupError && (
        <p className="rounded-lg bg-error-light px-3 py-2 text-xs text-error-dark" role="alert">
          {lookupError}
        </p>
      )}

      {hits.length > 0 && (
        <ul className="max-h-36 space-y-1.5 overflow-y-auto">
          {hits.map((hit) => (
            <li key={hit.id}>
              <button
                type="button"
                onClick={() => goToAsset(hit.id)}
                className="flex w-full flex-col rounded-lg border border-neutral-200 bg-neutral-0 px-3 py-2 text-start hover:border-primary-300"
              >
                <span className="text-sm font-semibold text-neutral-900">{hit.name}</span>
                <span className="text-xs text-neutral-500">
                  {[hit.label_code, hit.site_name].filter(Boolean).join(" · ")}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <Link to="/assets" className="text-center text-xs font-medium text-primary-700 hover:underline">
        {t("scan_browse_assets")}
      </Link>

      <style>{`
        .orbit-qr-viewfinder,
        .orbit-qr-viewfinder > div,
        .orbit-qr-viewfinder #${SCANNER_REGION_ID}__scan_region,
        .orbit-qr-viewfinder #${SCANNER_REGION_ID}__dashboard_section {
          width: 100% !important;
          height: 100% !important;
          max-height: ${VIEWFINDER_PX}px !important;
          margin: 0 !important;
          padding: 0 !important;
          border: none !important;
          background: transparent !important;
        }
        .orbit-qr-viewfinder video,
        .orbit-qr-viewfinder canvas {
          width: 100% !important;
          height: 100% !important;
          max-height: ${VIEWFINDER_PX}px !important;
          object-fit: cover !important;
          border-radius: 0.75rem;
        }
        .orbit-qr-viewfinder img {
          display: none !important;
        }
      `}</style>
    </div>
  );
}
