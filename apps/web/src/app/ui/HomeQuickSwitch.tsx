"use client";

import { useMemo, useState } from "react";
import DayEvents from "./DayEvents";
import { addDays, startOfWeekend, toYmd } from "@/lib/dates";

type View = "today" | "tomorrow" | "weekend";

export default function HomeQuickSwitch() {
  const [view, setView] = useState<View>("today");

  const day = useMemo(() => {
    const now = new Date();
    if (view === "today") return toYmd(now);
    if (view === "tomorrow") return toYmd(addDays(now, 1));
    return toYmd(startOfWeekend(now));
  }, [view]);

  return (
    <section style={{ marginTop: 24 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button onClick={() => setView("today")} aria-pressed={view === "today"}>
          Today
        </button>
        <button onClick={() => setView("tomorrow")} aria-pressed={view === "tomorrow"}>
          Tomorrow
        </button>
        <button onClick={() => setView("weekend")} aria-pressed={view === "weekend"}>
          Weekend
        </button>
      </div>

      <DayEvents day={day} />
    </section>
  );
}
