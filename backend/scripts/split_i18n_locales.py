#!/usr/bin/env python3
"""Extract ar/en translation objects from i18n/index.ts to JSON (NT-CLEAN-22)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "src" / "i18n" / "index.ts"
LOCALES = ROOT / "src" / "i18n" / "locales"


def extract_block(content: str, lang: str) -> dict[str, str]:
    pattern = rf"{lang}:\s*\{{\s*translation:\s*\{{(.*?)\n\s*\}},\n"
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        raise SystemExit(f"Could not find {lang} translation block")
    block = m.group(1)
    out: dict[str, str] = {}
    # key: "value" or key:\n      "value"
    for km in re.finditer(
        r"(\w+):\s*(?:\n\s*)?\"((?:\\.|[^\"\\])*)\"\s*,?",
        block,
    ):
        key = km.group(1)
        val = km.group(2).replace('\\"', '"').replace("\\n", "\n")
        out[key] = val
    return out


def main() -> None:
    content = INDEX.read_text(encoding="utf-8")
    LOCALES.mkdir(parents=True, exist_ok=True)
    ar = extract_block(content, "ar")
    en = extract_block(content, "en")
    only_ar = set(ar) - set(en)
    only_en = set(en) - set(ar)
    if only_ar:
        print("warn ar-only keys:", sorted(only_ar))
    if only_en:
        print("warn en-only keys:", sorted(only_en))

    for lang, data in (("ar", ar), ("en", en)):
        path = LOCALES / f"{lang}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(data)} keys)")

    INDEX.write_text(
        '''import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import ar from "./locales/ar.json";
import en from "./locales/en.json";

const resources = {
  ar: { translation: ar },
  en: { translation: en },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "ar",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
''',
        encoding="utf-8",
    )
    print("updated index.ts")


if __name__ == "__main__":
    main()
