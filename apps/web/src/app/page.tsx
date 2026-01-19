import HomeQuickSwitch from "./ui/HomeQuickSwitch";
import WeeklyEvents from "./ui/WeeklyEvents";

export default function HomePage() {
  return (
    <main style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>SRQ Happenings</h1>
      <HomeQuickSwitch />
      <WeeklyEvents start="2026-01-12" end="2026-01-18" title="This week in Sarasota" />
    </main>
  );
}
