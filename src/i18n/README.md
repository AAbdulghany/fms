# i18n

Translations live in JSON locale files:

- `locales/ar.json` — Arabic (default UI language)
- `locales/en.json` — English fallback

`index.ts` loads both into i18next. Add keys to **both** files when introducing new UI strings.

Regenerate from a monolith (if needed): `python backend/scripts/split_i18n_locales.py`
