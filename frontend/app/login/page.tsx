"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { safeRedirect } from "@/lib/navigation";
import { Eye, EyeOff, Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import ApexLogo from "@/components/ApexLogo";
import { useBrand } from "@/components/BrandProvider";

function LoginForm() {
  const router = useRouter();
  const { playIntroTransition } = useBrand();
  const searchParams = useSearchParams();
  const rawRedirect = searchParams.get("redirect") || searchParams.get("next") || searchParams.get("returnUrl");
  const targetUrl = safeRedirect(rawRedirect);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");

  useEffect(() => {
    // Pre-warm the backend immediately upon visitor arrival to reduce perceived cold starts
    void api.checkHealth();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (loading) return;
    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    setError("");
    setInfoMessage("");

    const wakeTimer = setTimeout(() => {
      setInfoMessage("Connecting to live backend... (Cloud instance wakes up from cold sleep in ~30s)");
    }, 2000);

    try {
      await api.login({ email, password });
      clearTimeout(wakeTimer);
      // Play brand intro animation in between login and entering the platform
      playIntroTransition(() => {
        router.push(targetUrl);
      });
    } catch (err) {
      clearTimeout(wakeTimer);
      setError(err instanceof Error ? err.message : "Invalid email or password.");
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setEmail("test@example.com");
    setPassword("password123");
    setError("");
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: 15 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className="w-full max-w-md rounded-3xl border border-[#EADBCE] bg-white/95 backdrop-blur-2xl p-8 sm:p-10 shadow-xl relative z-10"
    >
      {/* Header with Tree Artwork */}
      <div className="text-center mb-7">
        <div className="mx-auto mb-3 flex items-center justify-center">
          <ApexLogo variant="tree" size={130} />
        </div>
        <div className="mt-1">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-[0.25em] text-[#3D2331] uppercase select-none font-sans">
            ΛPEX
          </h1>
          <p className="mt-1 text-[10px] uppercase font-bold tracking-[0.25em] text-[#59414E]/80">
            Rooted in knowledge. Rising to intelligence.
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="login-email" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#3D2331]">
            Email Address
          </label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            required
            className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="login-password" className="block text-xs font-bold uppercase tracking-wider text-[#3D2331]">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs font-semibold text-[#087F5B] hover:text-[#066145] hover:underline transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 pr-11 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
            />
            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#7E6875] hover:text-[#3D2331] transition-colors"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {infoMessage && (
          <div className="rounded-xl border border-[#F4B942]/40 bg-[#F4B942]/15 p-3 text-xs text-[#9C6D08] font-medium flex items-center gap-2">
            <Sparkles size={14} className="shrink-0 text-[#D49520]" />
            <span>{infoMessage}</span>
          </div>
        )}

        {error && (
          <div role="alert" className="rounded-xl border border-[#E76F51]/30 bg-[#E76F51]/10 p-3 text-xs text-[#C84F33] font-medium flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E76F51] animate-pulse shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          aria-label="Sign In to Operations"
          className="w-full rounded-xl bg-[#087F5B] hover:bg-[#066649] py-3.5 text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Authenticating...</span>
            </>
          ) : (
            <span>Sign In to Platform</span>
          )}
        </button>

        {/* Quick fill demo credentials pill */}
        {process.env.NEXT_PUBLIC_ENABLE_DEMO_ACCOUNT === "true" && <button
          type="button"
          aria-label="Auto-fill demo credentials"
          onClick={handleFillDemo}
          className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/60 hover:bg-[#F7F3E8] py-2.5 text-xs font-semibold text-[#59414E] hover:text-[#3D2331] transition-colors flex items-center justify-center gap-2 shadow-2xs"
        >
          <CheckCircle2 size={13} className="text-[#087F5B]" />
          <span>Fill Demo Credentials (test@example.com)</span>
        </button>}
      </form>

      {/* Footer */}
      <div className="mt-8 text-center text-xs text-[#59414E]">
        Don&apos;t have an account?{" "}
        <Link
          href={targetUrl !== "/" ? `/register?redirect=${encodeURIComponent(targetUrl)}` : "/register"}
          className="font-bold text-[#087F5B] hover:underline"
        >
          Register now
        </Link>
      </div>
    </motion.div>
  );
}

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12 overflow-hidden bg-[#F7F3E8]">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-[#F4B942]/15 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-80 w-80 rounded-full bg-[#E76F51]/10 blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 h-80 w-80 rounded-full bg-[#087F5B]/10 blur-3xl pointer-events-none" />

      <Suspense fallback={
        <div className="w-full max-w-md rounded-3xl border border-[#EADBCE] bg-white/90 p-12 text-center text-[#59414E]">
          <Loader2 size={32} className="animate-spin text-[#087F5B] mx-auto mb-3" />
          <p className="text-xs">Loading sign-in portal...</p>
        </div>
      }>
        <LoginForm />
      </Suspense>
    </div>
  );
}
