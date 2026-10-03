"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface BrandIntroProps {
  onComplete?: () => void;
  forceShow?: boolean;
}

export default function BrandIntro({ onComplete, forceShow = false }: BrandIntroProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  const handleDismiss = useCallback(() => {
    try {
      sessionStorage.setItem("apex_intro_seen", "true");
    } catch {
      // Ignore in private modes
    }
    setIsVisible(false);
    if (onComplete) onComplete();
  }, [onComplete]);

  useEffect(() => {
    // Check reduced motion preference
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setIsReducedMotion(mediaQuery.matches);

      if (mediaQuery.matches && !forceShow) {
        handleDismiss();
        return;
      }

      // Check session storage
      const seen = sessionStorage.getItem("apex_intro_seen");
      if (seen && !forceShow) {
        setIsVisible(false);
        if (onComplete) onComplete();
        return;
      }

      setIsVisible(true);

      // Total sequence: 2.6s -> auto-dismiss
      const timer = setTimeout(() => {
        handleDismiss();
      }, 2650);

      // Escape key to skip
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape" || e.key === " ") {
          handleDismiss();
        }
      };
      window.addEventListener("keydown", handleKeyDown);

      return () => {
        clearTimeout(timer);
        window.removeEventListener("keydown", handleKeyDown);
      };
    }
  }, [forceShow, handleDismiss, onComplete]);

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="apex-brand-intro"
        initial={{ opacity: 1 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
        className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-[#F7F3E8] overflow-hidden select-none"
        aria-live="polite"
        role="region"
        aria-label="APEX Brand Introduction Animation"
      >
        {/* Subtle warm organic ambient background lighting */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-radial from-[#F4B942]/15 via-[#EADBCE]/30 to-transparent blur-3xl pointer-events-none" />

        {/* Skip Button */}
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Skip opening animation"
          className="absolute top-6 right-6 z-20 flex items-center gap-1.5 px-4 py-2 rounded-full border border-[#3D2331]/15 bg-[#F7F3E8]/80 backdrop-blur-md text-xs font-semibold text-[#3D2331] hover:bg-[#3D2331]/5 hover:border-[#3D2331]/30 transition-all active:scale-95 shadow-sm"
        >
          <span>Skip</span>
          <span className="text-[10px] text-[#59414E]/60 font-mono tracking-tighter">(ESC)</span>
        </button>

        {/* Layered Animated Growth SVG */}
        <div className="relative z-10 flex flex-col items-center justify-center max-w-sm sm:max-w-md w-full px-4">
          <svg
            viewBox="0 0 300 240"
            className="w-64 sm:w-80 h-auto overflow-visible"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <linearGradient id="intro-gold" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FFE082" />
                <stop offset="50%" stopColor="#F4B942" />
                <stop offset="100%" stopColor="#D49520" />
              </linearGradient>
              <linearGradient id="intro-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#20C997" />
                <stop offset="60%" stopColor="#087F5B" />
                <stop offset="100%" stopColor="#055B40" />
              </linearGradient>
              <linearGradient id="intro-coral" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#F4A261" />
                <stop offset="100%" stopColor="#E76F51" />
              </linearGradient>
              <linearGradient id="intro-plum" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#523143" />
                <stop offset="100%" stopColor="#3D2331" />
              </linearGradient>
              <filter id="intro-glow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* 0.0 - 0.4s: Golden Seed at the center */}
            <motion.g
              initial={{ scale: 0, opacity: 0 }}
              animate={{
                scale: isReducedMotion ? 1 : [0, 1.25, 1],
                opacity: [0, 1, 1],
              }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              style={{ originX: "150px", originY: "140px" }}
            >
              <ellipse cx="150" cy="140" rx="9" ry="14" fill="url(#intro-gold)" filter="url(#intro-glow)" />
              <circle cx="150" cy="140" r="18" stroke="url(#intro-gold)" strokeWidth="1" opacity="0.6" />
            </motion.g>

            {/* 0.4 - 1.2s: Roots Draw Downward */}
            <g stroke="url(#intro-gold)" strokeLinecap="round">
              <motion.path
                d="M 150 148 C 140 162 110 178 70 174"
                strokeWidth="3.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.4, ease: "easeInOut" }}
              />
              <motion.path
                d="M 150 148 C 142 168 126 182 105 186"
                strokeWidth="2.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.65, delay: 0.45, ease: "easeInOut" }}
              />
              <motion.path
                d="M 150 148 C 160 162 190 178 230 174"
                strokeWidth="3.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.4, ease: "easeInOut" }}
              />
              <motion.path
                d="M 150 148 C 158 168 174 182 195 186"
                strokeWidth="2.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.65, delay: 0.45, ease: "easeInOut" }}
              />
            </g>

            {/* 0.4 - 1.2s: Trunk & Branches Draw Upward */}
            <g stroke="url(#intro-plum)" strokeLinecap="round" strokeLinejoin="round" fill="none">
              <motion.path
                d="M 130 152 C 134 122 144 110 150 88 C 156 110 166 122 170 152"
                strokeWidth="8.5"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.75, delay: 0.42, ease: "easeInOut" }}
              />
              <motion.path
                d="M 150 96 C 136 76 106 72 82 86 M 150 96 C 164 76 194 72 218 86"
                strokeWidth="6"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.65, delay: 0.65, ease: "easeInOut" }}
              />
              <motion.path
                d="M 150 82 C 140 60 120 52 100 60 M 150 82 C 160 60 180 52 200 60"
                strokeWidth="4.5"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.6, delay: 0.75, ease: "easeInOut" }}
              />
            </g>

            {/* 1.2 - 1.7s: Emerald Leaves Appear */}
            <motion.path
              d="M 82 86 C 60 82 54 62 76 56 C 96 62 92 82 82 86 Z"
              fill="url(#intro-emerald)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, delay: 1.22, ease: "backOut" }}
              style={{ originX: "82px", originY: "86px" }}
            />
            <motion.path
              d="M 218 86 C 240 82 246 62 224 56 C 204 62 208 82 218 86 Z"
              fill="url(#intro-emerald)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, delay: 1.25, ease: "backOut" }}
              style={{ originX: "218px", originY: "86px" }}
            />
            <motion.path
              d="M 124 46 C 110 32 114 12 132 14 C 142 26 138 40 124 46 Z"
              fill="url(#intro-emerald)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, delay: 1.3, ease: "backOut" }}
              style={{ originX: "124px", originY: "46px" }}
            />
            <motion.path
              d="M 176 46 C 190 32 186 12 168 14 C 158 26 162 40 176 46 Z"
              fill="url(#intro-emerald)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, delay: 1.32, ease: "backOut" }}
              style={{ originX: "176px", originY: "46px" }}
            />

            {/* 1.2 - 1.7s: Coral Accent Leaves Appear */}
            <motion.path
              d="M 100 60 C 86 46 92 30 108 34 C 116 46 112 56 100 60 Z"
              fill="url(#intro-coral)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.38, delay: 1.34, ease: "backOut" }}
              style={{ originX: "100px", originY: "60px" }}
            />
            <motion.path
              d="M 200 60 C 214 46 208 30 192 34 C 184 46 188 56 200 60 Z"
              fill="url(#intro-coral)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.38, delay: 1.36, ease: "backOut" }}
              style={{ originX: "200px", originY: "60px" }}
            />
            <motion.path
              d="M 112 104 C 94 112 80 98 86 86 C 100 86 110 94 112 104 Z"
              fill="url(#intro-coral)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.35, delay: 1.4, ease: "backOut" }}
              style={{ originX: "112px", originY: "104px" }}
            />
            <motion.path
              d="M 188 104 C 206 112 220 98 214 86 C 200 86 190 94 188 104 Z"
              fill="url(#intro-coral)"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.35, delay: 1.42, ease: "backOut" }}
              style={{ originX: "188px", originY: "104px" }}
            />

            {/* 1.2 - 1.7s: Golden Apex Crowning Leaf Glows */}
            <motion.g
              initial={{ scale: 0, opacity: 0 }}
              animate={{
                scale: isReducedMotion ? 1 : [0, 1.3, 1],
                opacity: 1,
              }}
              transition={{ duration: 0.45, delay: 1.4, ease: "easeOut" }}
              style={{ originX: "150px", originY: "38px" }}
            >
              <path
                d="M 150 4 C 132 24 136 48 150 56 C 164 48 168 24 150 4 Z"
                fill="url(#intro-gold)"
                filter="url(#intro-glow)"
              />
              <line x1="150" y1="14" x2="150" y2="48" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" opacity="0.9" />
              {/* Radiance circle */}
              <motion.circle
                cx="150"
                cy="30"
                r="30"
                fill="none"
                stroke="url(#intro-gold)"
                strokeWidth="1.5"
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: [0.5, 1.8], opacity: [0.8, 0] }}
                transition={{ duration: 0.8, delay: 1.5, repeat: 1, ease: "easeOut" }}
              />
            </motion.g>
          </svg>

          {/* 1.7 - 2.2s: APEX Wordmark & Tagline Fade In */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.48, delay: 1.7, ease: "easeOut" }}
            className="mt-6 text-center"
          >
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-[0.32em] text-[#3D2331] uppercase select-none font-sans flex items-center justify-center">
              <span className="inline-block transform scale-y-110">Λ</span>
              <span className="ml-2">P</span>
              <span className="ml-2">E</span>
              <span className="ml-2">X</span>
            </h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.9 }}
              transition={{ duration: 0.38, delay: 1.88 }}
              className="text-[10px] sm:text-xs font-bold uppercase tracking-[0.3em] text-[#59414E] mt-2 select-none"
            >
              Rooted in knowledge. Rising to intelligence.
            </motion.p>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
