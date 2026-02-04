import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,

  // Required for Docker production builds - creates a standalone output
  // that includes only the necessary files for deployment
  output: "standalone",
};

export default nextConfig;
