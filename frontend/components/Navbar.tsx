"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";
import type { User } from "@/types";
import { Zap, LogOut, Activity, User as UserIcon, Shield } from "lucide-react";
import { motion } from "framer-motion";

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);

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
    api.logout();
    router.push("/login");
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#090d16]/95 backdrop-blur-xl shadow-lg shadow-black/25"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-rose-500 text-white shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform duration-300">
            <Zap size={22} className="fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-extrabold tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                APEX AI
              </span>
              <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold text-indigo-400 border border-indigo-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Autonomous Multi-Agent Engine</p>
          </div>
        </Link>

        {/* Center / Status */}
        <div className="hidden md:flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/5">
          <span className="relative flex h-2 w-2">
            {isBackendHealthy && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isBackendHealthy ? "bg-emerald-400" : "bg-rose-500"
              }`}
            ></span>
          </span>
          <span className="text-slate-300">
            {isBackendHealthy ? "Backend Connected (FastAPI)" : "Connecting to Engine..."}
          </span>
        </div>

        {/* User Profile & Actions */}
        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/[0.03] border border-white/5 text-xs text-slate-300">
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-500/30 font-bold">
                {user.email.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium max-w-[130px] truncate">{user.email}</span>
            </div>
          )}

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-rose-500/10 hover:border-rose-500/30 hover:text-rose-400 transition-all duration-200"
          >
            <LogOut size={14} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </motion.header>
  );
}
