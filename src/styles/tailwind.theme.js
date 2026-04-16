/**
 * Tailwind theme extension — mirrors design tokens in tokens.css
 * Use utilities: bg-primary-500, text-status-in-progress, font-body-en, etc.
 */

export default {
  screens: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },

  colors: {
    primary: {
      50: "var(--color-primary-50)",
      100: "var(--color-primary-100)",
      200: "var(--color-primary-200)",
      300: "var(--color-primary-300)",
      400: "var(--color-primary-400)",
      500: "var(--color-primary-500)",
      600: "var(--color-primary-600)",
      700: "var(--color-primary-700)",
      800: "var(--color-primary-800)",
      900: "var(--color-primary-900)",
    },
    secondary: {
      50: "var(--color-secondary-50)",
      100: "var(--color-secondary-100)",
      200: "var(--color-secondary-200)",
      300: "var(--color-secondary-300)",
      400: "var(--color-secondary-400)",
      500: "var(--color-secondary-500)",
      600: "var(--color-secondary-600)",
      700: "var(--color-secondary-700)",
      800: "var(--color-secondary-800)",
      900: "var(--color-secondary-900)",
    },
    neutral: {
      0: "var(--color-neutral-0)",
      50: "var(--color-neutral-50)",
      100: "var(--color-neutral-100)",
      200: "var(--color-neutral-200)",
      300: "var(--color-neutral-300)",
      400: "var(--color-neutral-400)",
      500: "var(--color-neutral-500)",
      600: "var(--color-neutral-600)",
      700: "var(--color-neutral-700)",
      800: "var(--color-neutral-800)",
      900: "var(--color-neutral-900)",
    },
    success: {
      light: "var(--color-success-light)",
      DEFAULT: "var(--color-success-main)",
      dark: "var(--color-success-dark)",
    },
    warning: {
      light: "var(--color-warning-light)",
      DEFAULT: "var(--color-warning-main)",
      dark: "var(--color-warning-dark)",
    },
    error: {
      light: "var(--color-error-light)",
      DEFAULT: "var(--color-error-main)",
      dark: "var(--color-error-dark)",
    },
    info: {
      light: "var(--color-info-light)",
      DEFAULT: "var(--color-info-main)",
      dark: "var(--color-info-dark)",
    },
    status: {
      created: "var(--status-created)",
      assigned: "var(--status-assigned)",
      "in-progress": "var(--status-in-progress)",
      "on-hold": "var(--status-on-hold)",
      completed: "var(--status-completed)",
      verified: "var(--status-verified)",
      cancelled: "var(--status-cancelled)",
      rejected: "var(--status-rejected)",
    },
    urgency: {
      normal: "var(--urgency-normal)",
      urgent: "var(--urgency-urgent)",
      emergency: "var(--urgency-emergency)",
    },
  },

  fontFamily: {
    "display-en": ["var(--font-display-en)"],
    "body-en": ["var(--font-body-en)"],
    mono: ["var(--font-mono)"],
    "display-ar": ["var(--font-display-ar)"],
    "body-ar": ["var(--font-body-ar)"],
  },

  fontSize: {
    xs: ["var(--text-xs)", { lineHeight: "1rem" }],
    sm: ["var(--text-sm)", { lineHeight: "1.25rem" }],
    base: ["var(--text-base)", { lineHeight: "1.5rem" }],
    lg: ["var(--text-lg)", { lineHeight: "1.75rem" }],
    xl: ["var(--text-xl)", { lineHeight: "1.75rem" }],
    "2xl": ["var(--text-2xl)", { lineHeight: "2rem" }],
    "3xl": ["var(--text-3xl)", { lineHeight: "2.25rem" }],
    "4xl": ["var(--text-4xl)", { lineHeight: "2.5rem" }],
  },

  fontWeight: {
    display: "700",
    h1: "600",
    h2: "600",
    h3: "600",
    h4: "500",
    body: "400",
    overline: "600",
  },

  lineHeight: {
    display: "2.5rem",
    h1: "2.25rem",
    h2: "2rem",
    h3: "1.75rem",
    h4: "1.75rem",
  },

  borderRadius: {
    sm: "var(--radius-sm)",
    md: "var(--radius-md)",
    lg: "var(--radius-lg)",
    xl: "var(--radius-xl)",
    full: "var(--radius-full)",
  },

  boxShadow: {
    sm: "var(--shadow-sm)",
    md: "var(--shadow-md)",
    lg: "var(--shadow-lg)",
    xl: "var(--shadow-xl)",
  },
};
