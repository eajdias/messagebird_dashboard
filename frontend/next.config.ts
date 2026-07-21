import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  compiler: {
    // Keep console.* in production so Docker logs capture frontend output.
    removeConsole: false,
  },
};

export default nextConfig;
