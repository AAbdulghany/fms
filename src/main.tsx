import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";

import App from "./App";
import i18n, { i18nReady } from "./i18n";
import { applyLanguage, getStoredLanguage } from "@/lib/language";
import "./styles/globals.css";

void i18nReady.then(async () => {
  await applyLanguage(getStoredLanguage(), i18n);

  const tree = (
    <I18nextProvider i18n={i18n}>
      <App />
    </I18nextProvider>
  );

  createRoot(document.getElementById("root")!).render(
    // StrictMode double-invokes effects in development only (P15).
    import.meta.env.DEV ? <StrictMode>{tree}</StrictMode> : tree
  );
});
