/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Data is fetched at build time and committed as static JSON.
  // No runtime data calls -> safe to deploy as static + serverless.
  eslint: {
    ignoreDuringBuilds: false,
  },
};

export default nextConfig;
