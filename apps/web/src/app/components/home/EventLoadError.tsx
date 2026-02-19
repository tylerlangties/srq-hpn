"use client";

type Props = {
  message: string;
};

export default function EventLoadError({ message }: Props) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-5 dark:border-amber-400/30 dark:bg-amber-500/10">
      <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">Our event feed is out chasing seagulls.</p>
      <p className="mt-1 text-sm text-amber-800/90 dark:text-amber-100/80">
        {message} Please try again later.
      </p>
    </div>
  );
}
