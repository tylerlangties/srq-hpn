export type WeatherSummary = {
  date: string;
  temp: number | null;
  condition: string;
  icon: string;
  sunset?: string | null;
};

export type WeatherPayload = {
  today: WeatherSummary;
  tomorrow: WeatherSummary;
  weekend: WeatherSummary;
};

type OpenMeteoDaily = {
  time: string[];
  temperature_2m_max: number[];
  weathercode: number[];
  sunset: string[];
};

type OpenMeteoResponse = {
  daily: OpenMeteoDaily;
};

function weatherCodeToSummary(code: number): { condition: string; icon: string } {
  if (code === 0) return { condition: "clear", icon: "☀️" };
  if (code <= 2) return { condition: "partly cloudy", icon: "⛅" };
  if (code <= 3) return { condition: "cloudy", icon: "☁️" };
  if (code >= 45 && code <= 48) return { condition: "foggy", icon: "🌫️" };
  if (code >= 51 && code <= 67) return { condition: "drizzle", icon: "🌦️" };
  if (code >= 71 && code <= 77) return { condition: "snow", icon: "❄️" };
  if (code >= 80 && code <= 82) return { condition: "rain", icon: "🌧️" };
  if (code >= 95) return { condition: "stormy", icon: "⛈️" };
  return { condition: "pleasant", icon: "🌤️" };
}

function toLocalTimeLabel(iso: string): string {
  const dt = new Date(iso);
  return dt.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function buildSummary(
  daily: OpenMeteoDaily,
  index: number
): WeatherSummary {
  const temp = daily.temperature_2m_max[index];
  const weather = weatherCodeToSummary(daily.weathercode[index]);
  const sunset = daily.sunset[index];

  return {
    date: daily.time[index],
    temp: Number.isFinite(temp) ? Math.round(temp) : null,
    condition: weather.condition,
    icon: weather.icon,
    sunset: sunset ? toLocalTimeLabel(sunset) : null,
  };
}

function findNextWeekendIndex(dates: string[]): number | null {
  for (let i = 0; i < dates.length; i += 1) {
    const day = new Date(dates[i]).getDay();
    if (day === 6) return i;
  }
  return null;
}

export async function fetchWeather(): Promise<WeatherPayload> {
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.searchParams.set("latitude", "27.3364");
  url.searchParams.set("longitude", "-82.5307");
  url.searchParams.set("daily", "temperature_2m_max,weathercode,sunset");
  url.searchParams.set("timezone", "America/New_York");
  url.searchParams.set("temperature_unit", "fahrenheit");

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Weather API ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as OpenMeteoResponse;
  const daily = data.daily;

  const today = buildSummary(daily, 0);
  const tomorrow = buildSummary(daily, 1);
  const weekendIndex = findNextWeekendIndex(daily.time) ?? 2;
  const weekend = buildSummary(daily, weekendIndex);

  return { today, tomorrow, weekend };
}
