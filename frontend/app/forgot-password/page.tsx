"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { ArrowLeft, CheckCircle2, Eye, EyeOff, KeyRound, Loader2, Mail, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import ApexLogo from "@/components/ApexLogo";

function ForgotPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialToken = searchParams.get("token") || "";

  // Step state: "request" or "reset" or "success"
  const [step, setStep] = useState<"request" | "reset" | "success">(initialToken ? "reset" : "request");

  // Form states
  const [email, setEmail] = useState("");
  const [token, setToken] = useState(initialToken);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Status states
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialToken) {
      setToken(initialToken);
      setStep("reset");
    }
  }, [initialToken]);

  const handleRequestReset = async (e: FormEvent) => {
    e.preventDefault();
    if (loading) return;
    if (!email) {
      setError("Please enter your registered email address.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const res = await api.forgotPassword(email);
      setMessage(res.detail);
      if (res.reset_token) {
        setToken(res.reset_token);
        // Seamlessly transition to password reset step
        setStep("reset");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    if (loading) return;

    if (!token) {
      setError("Password reset token is missing. Please request a new link.");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await api.resetPassword(token, newPassword);
      setMessage(res.detail || "Your password has been successfully reset.");
      setStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset password. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <Link href="/" className="inline-flex items-center gap-3 group mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white border border-[#EADBCE] shadow-sm group-hover:scale-105 transition-transform duration-300">
            <ApexLogo variant="navbar" size={34} />
          </div>
          <span className="text-2xl font-extrabold tracking-[0.2em] text-[#3D2331]">
            ΛPEX
          </span>
        </Link>
        <h1 className="text-xl font-bold tracking-tight text-[#3D2331]">
          {step === "request" && "Recover Your Account"}
          {step === "reset" && "Set New Password"}
          {step === "success" && "Password Reset Complete"}
        </h1>
        <p className="text-xs text-[#59414E]/80 mt-1">
          {step === "request" && "Enter your email to receive recovery instructions."}
          {step === "reset" && "Create a secure new password for your account."}
          {step === "success" && "Your credentials have been securely updated."}
        </p>
      </div>

      {/* Main Card */}
      <div className="rounded-3xl border border-[#EADBCE] bg-white/70 backdrop-blur-xl p-8 shadow-sm">
        {/* Error Notification */}
        {error && (
          <div role="alert" className="rounded-xl border border-[#E76F51]/30 bg-[#E76F51]/10 p-3.5 text-xs text-[#C84F33] font-medium flex items-center gap-2 mb-6">
            <ShieldAlert size={16} className="shrink-0 text-[#E76F51]" />
            <span>{error}</span>
          </div>
        )}

        {/* Step 1: Request Reset */}
        {step === "request" && (
          <form onSubmit={handleRequestReset} className="space-y-5">
            <div>
              <label htmlFor="recovery-email" className="block text-xs font-bold uppercase tracking-wider text-[#3D2331] mb-1.5">
                Registered Email
              </label>
              <div className="relative">
                <input
                  id="recovery-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 pl-11 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
                />
                <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7E6875]" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#087F5B] hover:bg-[#066649] py-3.5 text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <KeyRound size={16} />
                  <span>Send Recovery Instructions</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* Step 2: Set New Password */}
        {step === "reset" && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            {message && (
              <div className="rounded-xl border border-[#087F5B]/20 bg-[#087F5B]/10 p-3 text-xs text-[#087F5B] font-medium flex items-center gap-2 mb-2">
                <CheckCircle2 size={14} className="shrink-0" />
                <span>Recovery token verified. Please enter your new password.</span>
              </div>
            )}

            <div>
              <label htmlFor="new-password" className="block text-xs font-bold uppercase tracking-wider text-[#3D2331] mb-1.5">
                New Password (min 8 characters)
              </label>
              <div className="relative">
                <input
                  id="new-password"
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 pr-11 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#7E6875] hover:text-[#3D2331]"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirm-password" className="block text-xs font-bold uppercase tracking-wider text-[#3D2331] mb-1.5">
                Confirm New Password
              </label>
              <input
                id="confirm-password"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
                className="w-full rounded-xl border border-[#EADBCE] bg-[#F7F3E8]/40 px-4 py-3 text-sm text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#087F5B] hover:bg-[#066649] py-3.5 text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2 mt-4"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Updating Password...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} />
                  <span>Update Password & Proceed</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* Step 3: Success */}
        {step === "success" && (
          <div className="text-center py-4 space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#087F5B]/10 text-[#087F5B]">
              <CheckCircle2 size={32} />
            </div>
            <p className="text-sm font-semibold text-[#3D2331]">
              {message || "Your password has been successfully updated."}
            </p>
            <p className="text-xs text-[#59414E]">
              You can now sign in using your new credentials.
            </p>
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="w-full rounded-xl bg-[#087F5B] hover:bg-[#066649] py-3.5 text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              Sign In to APEX
            </button>
          </div>
        )}

        {/* Back to Login Link */}
        <div className="mt-6 pt-5 border-t border-[#EADBCE] text-center">
          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#59414E] hover:text-[#3D2331] transition-colors"
          >
            <ArrowLeft size={13} />
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-[calc(100vh-80px)] items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full flex justify-center"
      >
        <Suspense
          fallback={
            <div className="rounded-3xl border border-[#EADBCE] bg-white/70 p-12 text-center flex flex-col items-center">
              <Loader2 size={32} className="text-[#087F5B] animate-spin mb-3" />
              <p className="text-xs text-[#59414E]">Loading password recovery...</p>
            </div>
          }
        >
          <ForgotPasswordForm />
        </Suspense>
      </motion.div>
    </div>
  );
}
