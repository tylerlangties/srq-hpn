type Props = {
  title: string;
  subtitle?: string;
  icon: string;
  tone?: "coral" | "palm" | "gulf";
  action?: React.ReactNode;
};

export default function SectionHeader({
  title,
  subtitle,
  icon,
  tone = "coral",
  action,
}: Props) {
  const toneClasses =
    tone === "palm"
      ? "bg-palm/10 text-palm dark:bg-emerald-500/20 dark:text-emerald-400"
      : tone === "gulf"
        ? "bg-gulf/10 text-gulf dark:bg-cyan-500/20 dark:text-cyan-400"
        : "bg-coral/10 text-coral dark:bg-purple-500/20 dark:text-purple-300";

  return (
    <div className="mb-6 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className={`h-8 w-8 rounded-lg grid place-items-center ${toneClasses}`}>
          <span className="text-sm">{icon}</span>
        </div>
        <div>
          <h2 className="text-2xl font-[var(--font-heading)] font-bold">
            {title}
          </h2>
          {subtitle ? (
            <p className="text-sm text-muted dark:text-white/50">{subtitle}</p>
          ) : null}
        </div>
      </div>
      {action ? <div className="w-full sm:w-auto sm:shrink-0">{action}</div> : null}
    </div>
  );
}
