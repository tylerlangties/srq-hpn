import { ImageResponse } from "next/og";

export const alt = "SRQ Happenings";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "56px",
          background: "linear-gradient(135deg, #0f766e 0%, #0f172a 100%)",
          color: "#f8fafc",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "14px",
            fontSize: "28px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            opacity: 0.9,
          }}
        >
          <span>SRQ Happenings</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "880px" }}>
          <span style={{ fontSize: "68px", lineHeight: 1.05, fontWeight: 700 }}>
            Sarasota events, every day.
          </span>
          <span style={{ fontSize: "34px", lineHeight: 1.2, opacity: 0.9 }}>
            Local happenings, venue picks, and weekend guides.
          </span>
        </div>

        <div style={{ display: "flex", fontSize: "24px", opacity: 0.88 }}>srqhappenings.com</div>
      </div>
    ),
    {
      ...size,
    }
  );
}
