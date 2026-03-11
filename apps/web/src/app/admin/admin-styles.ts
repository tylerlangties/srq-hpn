/**
 * Shared design system classes for admin pages.
 * Aligns admin UI with the public site palette: charcoal, coral, gulf, palm, sand, muted.
 */
export const adminStyles = {
  // Page container
  container: "container mx-auto max-w-4xl px-4 py-8",
  containerWide: "container mx-auto max-w-6xl px-4 py-8",

  // Headings
  pageTitle: "text-3xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white",
  sectionTitle: "text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white",
  bodyText: "text-sm text-muted dark:text-white/60",
  label: "block text-xs font-semibold text-charcoal dark:text-white/80",

  // Cards
  card: "rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm",
  cardMuted: "rounded-2xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-4",

  // Form controls
  input:
    "w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30",
  inputDisabled:
    "w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/80 dark:bg-white/5 text-muted dark:text-white/50 px-3 py-2 text-sm",

  // Buttons
  btnPrimary:
    "rounded-xl bg-gulf px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-gulf/90 disabled:opacity-50 disabled:cursor-not-allowed",
  btnSecondary:
    "rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white transition-colors hover:bg-sand/80 dark:hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed",
  btnDestructive:
    "rounded-xl bg-coral px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-coral/90 disabled:opacity-50 disabled:cursor-not-allowed",
  btnSuccess:
    "rounded-xl bg-palm px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-palm/90 disabled:opacity-50 disabled:cursor-not-allowed",

  // States
  loading: "text-sm text-muted dark:text-white/50 font-medium",
  successBox:
    "rounded-xl border border-palm/30 dark:border-palm/40 bg-palm/10 dark:bg-palm/20 p-4",
  successText: "text-sm font-semibold text-palm dark:text-palm/90",
  errorBox:
    "rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4",
  errorText: "text-sm font-semibold text-red-700 dark:text-red-300",
  errorTextMuted: "text-sm text-red-800 dark:text-red-400",
  warningBox:
    "rounded-xl border border-coral/40 dark:border-coral/50 bg-coral/10 dark:bg-coral/20 p-4",

  // Badges
  badgeSuccess: "rounded-full bg-palm/15 px-2 py-0.5 text-xs font-semibold text-palm dark:bg-palm/25 dark:text-palm/90",
  badgeWarning: "rounded-full bg-coral/15 px-2 py-0.5 text-xs font-semibold text-coral dark:bg-coral/25 dark:text-coral-300",
  badgeHidden: "rounded-full bg-coral/15 px-2 py-0.5 text-xs font-medium text-coral dark:bg-coral/25 dark:text-coral-300",

  // Link cards
  linkCard:
    "block rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm transition-all hover:shadow-md",
  linkCardVenue: "hover:border-palm/40 dark:hover:border-palm/50 hover:bg-palm/5 dark:hover:bg-palm/10",
  linkCardUnresolved: "hover:border-gulf/40 dark:hover:border-gulf/50 hover:bg-gulf/5 dark:hover:bg-gulf/10",
  linkCardTasks: "hover:border-gulf/40 dark:hover:border-gulf/50 hover:bg-gulf/5 dark:hover:bg-gulf/10",

  // List items
  listItem:
    "rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-3",
} as const;
