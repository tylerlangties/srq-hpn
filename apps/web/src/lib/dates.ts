export function toYmd(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function addDays(d: Date, days: number): Date {
  const copy = new Date(d);
  copy.setDate(copy.getDate() + days);
  return copy;
}

export function startOfWeekend(d: Date): Date {
  // Weekend = Saturday/Sunday. Find next Saturday (or today if Saturday).
  const copy = new Date(d);
  const dow = copy.getDay(); // 0 Sun ... 6 Sat
  const daysUntilSat = (6 - dow + 7) % 7;
  copy.setDate(copy.getDate() + daysUntilSat);
  return copy;
}
