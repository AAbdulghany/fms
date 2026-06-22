/**
 * User-facing API error resolution (NT-131).
 * Prefers bilingual messages from API; falls back to i18n; never shows raw SCREAMING_SNAKE to users.
 */

export type ApiErrorDetail =
  | string
  | {
      code?: string;
      message_en?: string;
      message_ar?: string;
      missing_fields?: string[];
    };

export type ApiErrorBody = {
  detail?: ApiErrorDetail;
};

function parseErrorBody(err: unknown): ApiErrorBody | null {
  const raw = err instanceof Error ? err.message : String(err);
  try {
    return JSON.parse(raw) as ApiErrorBody;
  } catch {
    return null;
  }
}

function isArabicLocale(lang: string): boolean {
  return lang.startsWith("ar");
}

function messageFromDetail(detail: ApiErrorDetail, lang: string): string | null {
  if (typeof detail === "string") return null;
  const ar = isArabicLocale(lang);
  if (ar && detail.message_ar) return detail.message_ar;
  if (!ar && detail.message_en) return detail.message_en;
  if (detail.message_en) return detail.message_en;
  if (detail.message_ar) return detail.message_ar;
  return null;
}

function codeFromDetail(detail: ApiErrorDetail | undefined): string | null {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  return detail.code ?? null;
}

/** Resolve API error to a user-facing string (bilingual API → i18n → soft fallback). */
export function resolveApiError(
  err: unknown,
  t: (key: string) => string,
  lang: string,
  fallback = "Something went wrong. Please try again."
): string {
  const body = parseErrorBody(err);
  const detail = body?.detail;

  if (detail) {
    const fromApi = messageFromDetail(detail, lang);
    if (fromApi) return fromApi;

    const code = codeFromDetail(detail);
    if (code) {
      const key = `error_${code.toLowerCase()}`;
      const translated = t(key);
      if (translated !== key) return translated;
      return code.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }

    if (typeof detail === "string") {
      const key = `error_${detail.toLowerCase()}`;
      const translated = t(key);
      if (translated !== key) return translated;
      if (/^[A-Z][A-Z0-9_]+$/.test(detail)) {
        return detail.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
      }
      return detail;
    }

    if (typeof detail === "object" && detail.missing_fields?.length) {
      const fields = detail.missing_fields.join(", ");
      const key = "error_validation_missing_fields";
      const translated = t(key);
      return translated !== key ? `${translated}: ${fields}` : `Missing required fields: ${fields}`;
    }
  }

  const raw = err instanceof Error ? err.message : String(err);
  if (raw.length > 200) return fallback;
  return raw || fallback;
}

/** @deprecated Use resolveApiError(err, t, lang) for user-visible text. */
export function parseApiError(err: unknown, fallback = "Error"): string {
  const body = parseErrorBody(err);
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    if (detail.message_en) return detail.message_en;
    if (detail.code) return detail.code;
  }
  const raw = err instanceof Error ? err.message : String(err);
  return raw || fallback;
}
