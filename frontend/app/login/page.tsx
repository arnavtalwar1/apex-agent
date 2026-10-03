"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Zap, Eye, EyeOff, Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawRedirect = searchParams.get("redirect") || searchParams.get("next") || searchParams.get("returnUrl");
  const targetUrl = rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")
    ? rawRedirect
    : "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
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
      router.push(targetUrl);
    } catch (err) {
      clearTimeout(wakeTimer);
      setError(err instanceof Error ? err.message : "Invalid email or password.");
    } finally {
      clearTimeout(wakeTimer);
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
      className="w-full max-w-md rounded-3xl border border-white/10 bg-[#0d1527]/85 backdrop-blur-2xl p-8 sm:p-10 shadow-2xl relative z-10"
    >
      {/* Header */}
      <div className="text-center mb-8">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-rose-500 text-white shadow-xl shadow-indigo-500/25">
          <Zap size={28} className="fill-current" />
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Welcome to APEX AI
        </h1>
        <p className="mt-1.5 text-xs text-slate-400">
          Autonomous Multi-Agent Task Orchestration
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="login-email" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-300">
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
            className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="login-password" className="block text-xs font-bold uppercase tracking-wider text-slate-300">
              Password
            </label>
            <button
              type="button"
              aria-label="Forgot password help"
              onClick={() => setInfoMessage("In local mode, default demo account is test@example.com / password123.")}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Forgot Password?
            </button>
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
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 pr-11 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all"
            />
            <button
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {infoMessage && (
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/40 p-3 text-xs text-indigo-300 font-medium flex items-center gap-2">
            <Sparkles size={14} className="shrink-0 text-indigo-400" />
            <span>{infoMessage}</span>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 p-3 text-xs text-rose-300 font-medium flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          aria-label="Sign In to Operations"
          className="w-full rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-rose-500 hover:from-indigo-500 hover:to-rose-400 py-3.5 text-sm font-bold text-white shadow-xl shadow-indigo-500/25 disabled:opacity-50 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Authenticating...</span>
            </>
          ) : (
            <span>Sign In</span>
          )}
        </button>

        {/* Quick fill demo credentials pill */}
        <button
          type="button"
          aria-label="Auto-fill demo credentials"
          onClick={handleFillDemo}
          className="w-full rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.06] py-2.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors flex items-center justify-center gap-2"
        >
          <CheckCircle2 size={13} className="text-emerald-400" />
          <span>Fill Demo Credentials (test@example.com)</span>
        </button>
      </form>

      {/* Footer */}
      <div className="mt-8 text-center text-xs text-slate-400">
        Don&apos;t have an account?{" "}
        <Link
          href={targetUrl !== "/" ? `/register?redirect=${encodeURIComponent(targetUrl)}` : "/register"}
          className="font-bold text-indigo-400 hover:underline"
        >
          Register now
        </Link>
      </div>
    </motion.div>
  );
}

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12 overflow-hidden bg-[#090d16]">
      {/* Dynamic background glow orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-indigo-600/15 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-80 w-80 rounded-full bg-rose-600/10 blur-3xl pointer-events-none" />

      <Suspense fallback={
        <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#0d1527]/85 p-12 text-center text-slate-400">
          <Loader2 size={32} className="animate-spin text-indigo-400 mx-auto mb-3" />
          <p className="text-xs">Loading sign-in portal...</p>
        </div>
      }>
        <LoginForm />
      </Suspense>
    </div>
  );
}
