import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAccessToken } from "@/lib/api";

type PublicTag = {
  token: string;
  name: string;
  client_name?: string | null;
  site_name: string;
  can_report: boolean;
  asset_id?: string | null;
  has_history?: boolean;
};

export default function AssetTagLandingPage() {
  const { token = "" } = useParams<{ token: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [tag, setTag] = useState<PublicTag | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [contact, setContact] = useState("");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const headers: HeadersInit = {};
        const access = getAccessToken();
        if (access) headers.Authorization = `Bearer ${access}`;
        const res = await fetch(`/api/v1/public/asset-tags/${encodeURIComponent(token)}`, {
          headers,
        });
        if (!res.ok) {
          if (!cancelled) setError(t("tag_not_found"));
          return;
        }
        const data = (await res.json()) as PublicTag;
        if (cancelled) return;
        if (data.asset_id && access) {
          navigate(`/assets/${data.asset_id}`, { replace: true });
          return;
        }
        setTag(data);
      } catch {
        if (!cancelled) setError(t("error"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, navigate, t]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!tag || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/public/asset-tags/${encodeURIComponent(token)}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          contact: contact.trim() || undefined,
        }),
      });
      if (res.status === 429) {
        setError(t("report_rate_limited"));
        return;
      }
      if (!res.ok) {
        setError(t("error"));
        return;
      }
      setDone(true);
    } catch {
      setError(t("error"));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 px-4 py-10">
      <div className="mx-auto w-full max-w-md rounded-xl border border-neutral-200 bg-neutral-0 p-6 shadow-sm">
        {error && !tag ? (
          <p className="text-center text-neutral-700">{error}</p>
        ) : done ? (
          <div className="space-y-2 text-center">
            <h1 className="text-xl font-semibold text-neutral-900">{t("report_submitted")}</h1>
          </div>
        ) : tag ? (
          <div className="space-y-5">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                {tag.client_name || t("assets")}
              </p>
              <h1 className="mt-1 text-2xl font-semibold text-neutral-900">{tag.name}</h1>
              <p className="mt-1 text-sm text-neutral-600">{tag.site_name}</p>
            </div>

            {tag.can_report && (
              <form className="space-y-3" onSubmit={onSubmit}>
                <h2 className="text-sm font-semibold text-neutral-900">{t("report_a_problem")}</h2>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">{t("title")}</label>
                  <input
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    minLength={3}
                    maxLength={200}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">
                    {t("description")}
                  </label>
                  <textarea
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                    minLength={3}
                    maxLength={4000}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">
                    {t("contact")} ({t("optional")})
                  </label>
                  <input
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
                    value={contact}
                    onChange={(e) => setContact(e.target.value)}
                    maxLength={320}
                  />
                </div>
                {error && <p className="text-sm text-error-dark">{error}</p>}
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
                >
                  {submitting ? t("loading") : t("submit_report")}
                </button>
              </form>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
