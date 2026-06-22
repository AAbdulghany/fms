/** Format monetary amounts for invoice display (Phase 3 multi-currency). */

const SYMBOLS: Record<string, string> = {
  EGP: "E£",
  SAR: "﷼",
  USD: "$",
  EUR: "€",
};

export function currencySymbol(code: string): string {
  return SYMBOLS[code] ?? code;
}

export function formatMoneyAmount(amount: string | number, currency: string, locale?: string): string {
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  if (Number.isNaN(n)) return String(amount);
  const loc = locale ?? (document.documentElement.lang === "ar" ? "ar-SA" : "en-US");
  try {
    return new Intl.NumberFormat(loc, {
      style: "currency",
      currency: currency.length === 3 ? currency : "SAR",
      minimumFractionDigits: 2,
    }).format(n);
  } catch {
    return `${currency} ${n.toFixed(2)}`;
  }
}
