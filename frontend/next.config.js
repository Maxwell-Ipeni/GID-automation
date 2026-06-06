const nextConfig = {
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/images/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/images/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
