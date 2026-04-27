/** @type {import('next').NextConfig} */
const nextConfig = {
    eslint: {
        ignoreDuringBuilds: true,
    },
    async rewrites() {
        return [
            {
                source: '/api/v1/:path*',
                destination: 'https://claritai-edtech-production.up.railway.app/api/v1/:path*',
            },
        ];
    },
};

export default nextConfig;
