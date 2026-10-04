"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getToken } from "@/lib/api";
import type { User } from "@/types";
import { LogOut, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import ApexLogo from "./ApexLogo";
import { useBrand } from "./BrandProvider";

export default function Navbar() {
  const { replayIntro } = useBrand();
  const [user, setUser] = useState<User | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    // Check backend health
    api.checkHealth()
      .then((isHealthy) => setIsBackendHealthy(isHealthy))
      .catch(() => setIsBackendHealthy(false));

    const token = getToken();
    if (!token) return;

    api.getMe()
      .then((u) => setUser(u))
      .catch(() => {
        // Backend or token issue
      });
  }, []);

  const handleLogout = () => {
    void api.logout();
  };

  return (
    <motion.header
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 w-full border-b border-[#EADBCE] bg-[#F7F3E8]/90 backdrop-blur-xl shadow-sm"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group select-none">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white border border-[#EADBCE] shadow-sm group-hover:shadow-md group-hover:scale-105 transition-all duration-300">
            <ApexLogo variant="navbar" size={32} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-extrabold tracking-[0.2em] text-[#3D2331] font-sans">
                ΛPEX
              </span>
              <span className="rounded-full bg-[#F4B942]/20 px-2 py-0.5 text-[10px] font-bold text-[#3D2331] border border-[#F4B942]/40">
                AI
              </span>
            </div>
            <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-[#59414E]/70 hidden sm:block">
              Rooted in knowledge. Rising to intelligence.
            </p>
          </div>
        </Link>

        {/* Center / Status */}
        <div className="hidden md:flex items-center gap-2 text-xs font-semibold px-3.5 py-1.5 rounded-full bg-white/70 border border-[#EADBCE] text-[#59414E]">
          <span className="relative flex h-2 w-2">
            {isBackendHealthy && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#087F5B] opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isBackendHealthy ? "bg-[#087F5B]" : "bg-[#E76F51]"
              }`}
            ></span>
          </span>
          <span className="text-[11px] font-medium text-[#3D2331]">
            {isBackendHealthy === null ? "Checking connection…" : isBackendHealthy ? "Engine online" : "Engine unavailable"}
          </span>
        </div>

        {/* User Profile & Actions */}
        <div className="flex items-center gap-2.5">
          {/* Replay Brand Intro Button */}
          <button
            type="button"
            onClick={replayIntro}
            aria-label="Replay APEX growth animation"
            title="Replay Brand Intro"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-[#EADBCE] bg-white/60 hover:bg-white text-xs font-medium text-[#59414E] hover:text-[#3D2331] transition-all"
          >
            <Sparkles size={13} className="text-[#F4B942]" />
            <span className="hidden sm:inline text-[11px]">Intro</span>
          </button>

          {user && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/70 border border-[#EADBCE] text-xs text-[#3D2331]">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#3D2331] text-[#F7F3E8] text-[11px] font-bold">
                {user.email.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium max-w-[130px] truncate">{user.email}</span>
            </div>
          )}

          <button
            type="button"
            aria-label="Logout"
            onClick={handleLogout}
            className="flex items-center gap-2 rounded-xl border border-[#EADBCE] bg-white/60 hover:bg-[#E76F51]/10 hover:border-[#E76F51]/40 hover:text-[#E76F51] px-3.5 py-1.5 text-xs font-bold text-[#59414E] transition-all duration-200"
          >
            <LogOut size={13} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </motion.header>
  );
}
