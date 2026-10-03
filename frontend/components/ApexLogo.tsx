"use client";

import React from "react";

interface ApexLogoProps {
  variant?: "full" | "tree" | "wordmark" | "navbar" | "favicon";
  size?: number;
  className?: string;
  showTagline?: boolean;
}

export default function ApexLogo({
  variant = "full",
  size = 40,
  className = "",
  showTagline = true,
}: ApexLogoProps) {
  // Simplified Tree for Navbar and compact badges
  if (variant === "navbar" || variant === "favicon") {
    return (
      <svg
        viewBox="0 0 100 100"
        width={size}
        height={size}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`shrink-0 ${className}`}
        aria-label="APEX Tree"
      >
        <defs>
          <linearGradient id="nav-gold" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFE082" />
            <stop offset="50%" stopColor="#F4B942" />
            <stop offset="100%" stopColor="#D49520" />
          </linearGradient>
          <linearGradient id="nav-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#20C997" />
            <stop offset="100%" stopColor="#087F5B" />
          </linearGradient>
          <linearGradient id="nav-coral" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F4A261" />
            <stop offset="100%" stopColor="#E76F51" />
          </linearGradient>
          <linearGradient id="nav-plum" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#523143" />
            <stop offset="100%" stopColor="#3D2331" />
          </linearGradient>
          <filter id="nav-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Roots */}
        <path
          d="M 50 82 C 45 88 32 94 20 93 M 50 82 C 48 89 40 96 32 97 M 50 82 C 55 88 68 94 80 93 M 50 82 C 52 89 60 96 68 97"
          stroke="url(#nav-gold)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Intertwined Trunk & Primary Branches */}
        <path
          d="M 40 84 C 42 70 48 64 50 52 C 52 64 58 70 60 84"
          fill="none"
          stroke="url(#nav-plum)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M 50 56 C 44 48 30 46 22 52 M 50 56 C 56 48 70 46 78 52"
          fill="none"
          stroke="url(#nav-plum)"
          strokeWidth="4.5"
          strokeLinecap="round"
        />
        <path
          d="M 50 48 C 45 38 36 34 29 38 M 50 48 C 55 38 64 34 71 38"
          fill="none"
          stroke="url(#nav-plum)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />

        {/* Emerald Leaves */}
        <path
          d="M 22 52 C 14 50 12 40 20 38 C 28 40 26 50 22 52 Z"
          fill="url(#nav-emerald)"
        />
        <path
          d="M 78 52 C 86 50 88 40 80 38 C 72 40 74 50 78 52 Z"
          fill="url(#nav-emerald)"
        />
        <path
          d="M 40 32 C 34 26 36 16 44 18 C 48 24 46 30 40 32 Z"
          fill="url(#nav-emerald)"
        />
        <path
          d="M 60 32 C 66 26 64 16 56 18 C 52 24 54 30 60 32 Z"
          fill="url(#nav-emerald)"
        />

        {/* Coral Accent Leaves */}
        <path
          d="M 29 38 C 24 32 26 24 33 26 C 36 32 34 36 29 38 Z"
          fill="url(#nav-coral)"
        />
        <path
          d="M 71 38 C 76 32 74 24 67 26 C 64 32 66 36 71 38 Z"
          fill="url(#nav-coral)"
        />
        <path
          d="M 33 58 C 26 62 20 56 22 50 C 28 50 32 54 33 58 Z"
          fill="url(#nav-coral)"
        />
        <path
          d="M 67 58 C 74 62 80 56 78 50 C 72 50 68 54 67 58 Z"
          fill="url(#nav-coral)"
        />

        {/* Pinnacle / Golden Apex Leaf */}
        <path
          d="M 50 6 C 42 16 44 28 50 32 C 56 28 58 16 50 6 Z"
          fill="url(#nav-gold)"
          filter="url(#nav-glow)"
        />
        <line x1="50" y1="12" x2="50" y2="28" stroke="#FFFFFF" strokeWidth="1" strokeLinecap="round" opacity="0.75" />
      </svg>
    );
  }

  // Standalone Tree (scalable vector)
  if (variant === "tree") {
    return (
      <svg
        viewBox="0 0 200 160"
        width={size}
        height={(size * 160) / 200}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="APEX Tree Emblem"
      >
        <defs>
          <linearGradient id="tree-gold" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFE699" />
            <stop offset="40%" stopColor="#F4B942" />
            <stop offset="100%" stopColor="#D49520" />
          </linearGradient>
          <linearGradient id="tree-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#20C997" />
            <stop offset="60%" stopColor="#087F5B" />
            <stop offset="100%" stopColor="#055B40" />
          </linearGradient>
          <linearGradient id="tree-coral" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#F4A261" />
            <stop offset="100%" stopColor="#E76F51" />
          </linearGradient>
          <linearGradient id="tree-trunk" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#523143" />
            <stop offset="100%" stopColor="#3D2331" />
          </linearGradient>
          <filter id="tree-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Roots */}
        <g stroke="url(#tree-gold)" strokeLinecap="round">
          <path d="M 100 135 C 90 144 65 152 40 150" strokeWidth="3" />
          <path d="M 100 135 C 92 147 80 156 65 158" strokeWidth="2.5" />
          <path d="M 100 135 C 85 142 55 146 30 144" strokeWidth="2" />
          <path d="M 100 135 C 110 144 135 152 160 150" strokeWidth="3" />
          <path d="M 100 135 C 108 147 120 156 135 158" strokeWidth="2.5" />
          <path d="M 100 135 C 115 142 145 146 170 144" strokeWidth="2" />
        </g>

        {/* Trunk & Intertwining Core */}
        <path
          d="M 85 138 C 88 115 96 105 100 88 C 104 105 112 115 115 138"
          fill="none"
          stroke="url(#tree-trunk)"
          strokeWidth="9"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M 100 95 C 90 80 68 76 52 86 M 100 95 C 110 80 132 76 148 86"
          fill="none"
          stroke="url(#tree-trunk)"
          strokeWidth="7"
          strokeLinecap="round"
        />
        <path
          d="M 100 82 C 92 64 78 58 64 64 M 100 82 C 108 64 122 58 136 64"
          fill="none"
          stroke="url(#tree-trunk)"
          strokeWidth="5"
          strokeLinecap="round"
        />

        {/* Emerald Leaves */}
        <path d="M 52 86 C 36 82 32 66 48 62 C 62 66 60 82 52 86 Z" fill="url(#tree-emerald)" />
        <path d="M 148 86 C 164 82 168 66 152 62 C 138 66 140 82 148 86 Z" fill="url(#tree-emerald)" />
        <path d="M 82 52 C 70 42 74 26 88 28 C 96 38 92 48 82 52 Z" fill="url(#tree-emerald)" />
        <path d="M 118 52 C 130 42 126 26 112 28 C 104 38 108 48 118 52 Z" fill="url(#tree-emerald)" />
        <path d="M 40 102 C 28 106 20 96 24 86 C 34 86 40 94 40 102 Z" fill="url(#tree-emerald)" />
        <path d="M 160 102 C 172 106 180 96 176 86 C 166 86 160 94 160 102 Z" fill="url(#tree-emerald)" />

        {/* Coral Accent Leaves */}
        <path d="M 64 64 C 54 54 58 42 70 44 C 76 54 72 60 64 64 Z" fill="url(#tree-coral)" />
        <path d="M 136 64 C 146 54 142 42 130 44 C 124 54 128 60 136 64 Z" fill="url(#tree-coral)" />
        <path d="M 72 96 C 58 102 48 92 52 82 C 62 82 70 88 72 96 Z" fill="url(#tree-coral)" />
        <path d="M 128 96 C 142 102 152 92 148 82 C 138 82 130 88 128 96 Z" fill="url(#tree-coral)" />

        {/* Pinnacle Golden Apex */}
        <path
          d="M 100 8 C 86 24 90 44 100 50 C 110 44 114 24 100 8 Z"
          fill="url(#tree-gold)"
          filter="url(#tree-glow)"
        />
        <line x1="100" y1="18" x2="100" y2="44" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
      </svg>
    );
  }

  // Geometric Wordmark
  if (variant === "wordmark") {
    return (
      <div className={`flex flex-col items-center justify-center ${className}`}>
        <div className="font-extrabold tracking-[0.28em] text-[#3D2331] text-2xl sm:text-3xl uppercase select-none font-sans flex items-center">
          <span className="inline-block transform scale-y-110">Λ</span>
          <span className="ml-2">P</span>
          <span className="ml-2">E</span>
          <span className="ml-2">X</span>
        </div>
        {showTagline && (
          <p className="text-[9px] sm:text-[10px] uppercase font-bold tracking-[0.3em] text-[#59414E]/80 mt-1 select-none text-center">
            Rooted in knowledge. Rising to intelligence.
          </p>
        )}
      </div>
    );
  }

  // Full Lockup: Tree + Geometric Wordmark + Tagline
  return (
    <div className={`flex flex-col items-center text-center ${className}`}>
      <ApexLogo variant="tree" size={size} />
      <div className="mt-3">
        <ApexLogo variant="wordmark" showTagline={showTagline} />
      </div>
    </div>
  );
}
