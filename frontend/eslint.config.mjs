import nextConfig from "eslint-config-next";

const config = Array.isArray(nextConfig) ? nextConfig : [nextConfig];

export default config;
