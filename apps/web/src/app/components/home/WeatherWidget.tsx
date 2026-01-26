import type { WeatherPayload } from "@/lib/weather";

type Props = {
  weather: WeatherPayload | null;
  loading?: boolean;
  error?: string | null;
};

function WeatherRow({
  label,
  temp,
  condition,
  icon,
  sunset,
}: {
  label: string;
  temp: number | null;
  condition: string;
  icon: string;
  sunset?: string | null;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/60 dark:border-white/10 bg-white/80 dark:bg-white/5 px-4 py-3">
      <div>
        <p className="text-xs font-semibold text-muted dark:text-white/50">{label}</p>
        <p className="text-sm font-semibold text-charcoal dark:text-white">
          {temp ?? "—"}° · {condition}
        </p>
        {sunset ? (
          <p className="text-xs text-muted dark:text-white/50">Sunset {sunset}</p>
        ) : null}
      </div>
      <span className="text-2xl">{icon}</span>
    </div>
  );
}

export default function WeatherWidget({ weather, loading, error }: Props) {
  if (loading) {
    return (
      <div className="relative rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-2xl backdrop-blur-sm">
        <div className="h-4 w-32 animate-pulse rounded bg-sand/70 dark:bg-white/10 mb-4" />
        <div className="space-y-3">
          <div className="h-16 animate-pulse rounded-2xl bg-sand/70 dark:bg-white/10" />
          <div className="h-16 animate-pulse rounded-2xl bg-sand/70 dark:bg-white/10" />
          <div className="h-16 animate-pulse rounded-2xl bg-sand/70 dark:bg-white/10" />
        </div>
      </div>
    );
  }

  if (error || !weather) {
    return (
      <div className="relative rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-2xl backdrop-blur-sm">
        <div className="text-sm text-muted dark:text-white/50">
          Weather unavailable
        </div>
        <p className="mt-2 text-xs text-muted dark:text-white/40">
          We’ll update this card when the forecast is ready.
        </p>
      </div>
    );
  }

  return (
    <div className="relative rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-2xl backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-muted dark:text-white/50 uppercase tracking-widest">
            Sarasota Weather
          </p>
          <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
            Today at a glance
          </h2>
        </div>
        <span className="text-3xl">{weather.today.icon}</span>
      </div>

      <div className="space-y-3">
        <WeatherRow label="Today" {...weather.today} />
        <WeatherRow label="Tomorrow" {...weather.tomorrow} />
        <WeatherRow label="Weekend" {...weather.weekend} />
      </div>
    </div>
  );
}
