import HomeQuickSwitch from "./ui/HomeQuickSwitch";
import WeeklyEvents from "./ui/WeeklyEvents";

export default function HomePage() {
  return (
    <main className="container mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">SRQ Happenings</h1>
      <div className="space-y-8">
        <HomeQuickSwitch />
        <WeeklyEvents start="2026-01-12" end="2026-01-18" title="This week in Sarasota" />
      </div>
    </main>
  );
}
