import type { NextConfig } from "next";

const nextConfig: NextConfig = {};

if (process.env.NODE_ENV === "development") {
	nextConfig.distDir = ".next-dev";
}

export default nextConfig;