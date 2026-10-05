import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import BrandProvider from "@/components/BrandProvider";
import Footer from "@/components/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "APEX - Rooted in Knowledge. Rising to Intelligence.",
  description: "Autonomous Multi-Agent AI Platform & Cognitive Orchestration Engine",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[var(--background)] text-[var(--foreground)] selection:bg-[#F4B942]/30 selection:text-[#3D2331]">
        <BrandProvider>
          <div className="flex-1 flex flex-col min-h-screen">
            <div className="flex-1">{children}</div>
            <Footer />
          </div>
        </BrandProvider>
      </body>
    </html>
  );
}
