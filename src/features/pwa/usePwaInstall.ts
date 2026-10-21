import { useEffect, useRef, useState } from "react";

const DISMISS_KEY = "orbit_pwa_install_dismissed";
const VISIT_KEY = "orbit_pwa_install_visits";
const SHOW_AFTER_VISITS = 2;
const DWELL_MS = 2500;

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

function isStandaloneDisplay(): boolean {
  if (typeof window === "undefined") return false;
  const media = window.matchMedia("(display-mode: standalone)").matches;
  const iosStandalone =
    "standalone" in navigator &&
    Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
  return media || iosStandalone;
}

function isIosDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  return (
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  );
}

function isNarrowViewport(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(max-width: 1023px)").matches;
}

function canOfferInstall(): boolean {
  if (isStandaloneDisplay()) return false;
  if (localStorage.getItem(DISMISS_KEY) === "1") return false;
  if (!isNarrowViewport()) return false;
  return true;
}

export type PwaInstallMode = "chromium" | "ios" | null;

export function usePwaInstall() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [mode, setMode] = useState<PwaInstallMode>(null);
  const deferredRef = useRef<BeforeInstallPromptEvent | null>(null);
  const dwellReady = useRef(false);
  const visitsOk = useRef(false);

  useEffect(() => {
    if (isStandaloneDisplay()) return;
    if (localStorage.getItem(DISMISS_KEY) === "1") return;

    const visits = Number(localStorage.getItem(VISIT_KEY) || "0") + 1;
    localStorage.setItem(VISIT_KEY, String(visits));
    visitsOk.current = visits >= SHOW_AFTER_VISITS;

    const tryShow = () => {
      if (!dwellReady.current || !visitsOk.current || !canOfferInstall()) return;

      if (deferredRef.current) {
        setMode("chromium");
        setVisible(true);
        return;
      }

      if (isIosDevice()) {
        setMode("ios");
        setVisible(true);
      }
    };

    const onBeforeInstall = (event: Event) => {
      event.preventDefault();
      const promptEvent = event as BeforeInstallPromptEvent;
      deferredRef.current = promptEvent;
      setDeferred(promptEvent);
      tryShow();
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstall);

    const timer = window.setTimeout(() => {
      dwellReady.current = true;
      tryShow();
    }, DWELL_MS);

    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
      window.clearTimeout(timer);
    };
  }, []);

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "1");
    setVisible(false);
  };

  const promptInstall = async () => {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    deferredRef.current = null;
    setDeferred(null);
    setVisible(false);
  };

  return { visible, mode, dismiss, promptInstall, canPrompt: Boolean(deferred) };
}
