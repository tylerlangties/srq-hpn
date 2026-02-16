import { ImageResponse } from "next/og";

export const alt = "SRQ Happenings";
export const size = {
  width: 1200,
  height: 600,
};
export const contentType = "image/png";

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "52px",
          background: "linear-gradient(140deg, #0b3b66 0%, #0f766e 100%)",
          color: "#f8fafc",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <div style={{ fontSize: "26px", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          SRQ Happenings
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", maxWidth: "900px" }}>
          <span style={{ fontSize: "64px", lineHeight: 1.05, fontWeight: 700 }}>
            Sarasota events worth sharing.
          </span>
          <span style={{ fontSize: "30px", lineHeight: 1.2, opacity: 0.92 }}>
            Discover what is happening today, tomorrow, and this weekend.
          </span>
        </div>
        <div style={{ fontSize: "22px", opacity: 0.88 }}>srqhappenings.com</div>
      </div>
    ),
    {
      ...size,
    }
  );
}
