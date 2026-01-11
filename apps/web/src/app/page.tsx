export default async function Home() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  let apiStatus: string;

  try {
    const res = await fetch(`${baseUrl}/api/health`, { cache: "no-store" });
    if (!res.ok) throw new Error(`API responded with ${res.status}`);
    const data = (await res.json()) as { ok: boolean; service?: string };
    apiStatus = data.ok ? `✅ API OK (${data.service ?? "api"})` : "⚠️ API not OK";
  } catch (e) {
    apiStatus = "❌ API unreachable (is FastAPI running on :8000?)";
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1>SRQ Happenings</h1>
      <p>{apiStatus}</p>
    </main>
  );
}

