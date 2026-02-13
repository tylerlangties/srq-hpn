import { apiGet } from "@/lib/api";
import { API_PATHS } from "@/lib/api-paths";

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

export async function fetchWeather(): Promise<WeatherPayload> {
  return apiGet<WeatherPayload>(API_PATHS.weather.summary);
}
