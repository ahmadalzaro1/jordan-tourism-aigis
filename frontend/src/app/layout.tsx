import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jordan Tourism AI-GIS",
  description: "AI-Enabled Geo-Analytics Platform for Jordan Tourism",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body style={{
        margin: 0, padding: 0,
        backgroundColor: "#000",
        color: "#f5f5f5",
        minHeight: "100vh",
        fontFamily: "'Geist', -apple-system, sans-serif",
      }}>
        {children}
      </body>
    </html>
  );
}
