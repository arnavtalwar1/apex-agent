"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import ApexLogo from "@/components/ApexLogo";
import { useBrand } from "@/components/BrandProvider";

function RegisterForm() {
  const router = useRouter();
  const { playIntroTransition } = useBrand();
  const searchParams = useSearchParams();
  const rawRedirect = searchParams.get("redirect") || searchParams.get("next") || searchParams.get("returnUrl");
  const targetUrl = rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")
    ? rawRedirect
    : "/";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await api.register({
        email,
        password,
        full_name: fullName || undefined,
      });

      await api.login({ email, password });
      // Play brand intro animation in between registration and entering the platform
      playIntroTransition(() => {
        router.push(targetUrl);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
      setLoading(false);
    }
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
          <ApexLogo variant="tree" size={120} />
        </div>
        <div className="mt-1">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-[0.2em] text-[#3D2331] uppercase select-none font-sans">
            Create Account
          </h1>
          <p className="mt-1 text-[10px] uppercase font-bold tracking-[0.25em] text-[#59414E]/80">
            Rooted in knowledge. Rising to intelligence.
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="reg-name" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#3D2331]">
            Full Name
          </label>
          <input
            id="reg-name"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Alex Doe"
            className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
          />
        </div>

        <div>
          <label htmlFor="reg-email" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#3D2331]">
            Email Address
          </label>
          <input
            id="reg-email"
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
          <label htmlFor="reg-password" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-[#3D2331]">
            Password
          </label>
          <div className="relative">
            <input
              id="reg-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
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

        {error && (
          <div className="rounded-xl border border-[#E76F51]/30 bg-[#E76F51]/10 p-3 text-xs text-[#C84F33] font-medium flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E76F51] animate-pulse shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          aria-label="Create Account & Get Started"
          className="w-full rounded-xl bg-[#087F5B] hover:bg-[#066649] py-3.5 text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2 mt-2"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Creating Account...</span>
            </>
          ) : (
            <span>Create Account</span>
          )}
        </button>
      </form>

      {/* Footer */}
      <div className="mt-8 text-center text-xs text-[#59414E]">
        Already have an account?{" "}
        <Link
          href={targetUrl !== "/" ? `/login?redirect=${encodeURIComponent(targetUrl)}` : "/login"}
          className="font-bold text-[#087F5B] hover:underline"
        >
          Sign In
        </Link>
      </div>
    </motion.div>
  );
}

export default function RegisterPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12 overflow-hidden bg-[#F7F3E8]">
      {/* Background glow orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-[#F4B942]/15 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-80 w-80 rounded-full bg-[#E76F51]/10 blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 h-80 w-80 rounded-full bg-[#087F5B]/10 blur-3xl pointer-events-none" />

      <Suspense fallback={
        <div className="w-full max-w-md rounded-3xl border border-[#EADBCE] bg-white/90 p-12 text-center text-[#59414E]">
          <Loader2 size={32} className="animate-spin text-[#087F5B] mx-auto mb-3" />
          <p className="text-xs">Loading registration portal...</p>
        </div>
      }>
        <RegisterForm />
      </Suspense>
    </div>
  );
}
