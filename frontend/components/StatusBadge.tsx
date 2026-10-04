import React from "react";

interface StatusBadgeProps {
  status: string;
}

interface StyleConfig {
  badge: string;
  dot: string;
  ping?: boolean;
}

const STATUS_CONFIG: Record<string, StyleConfig> = {
  pending: {
    badge: "bg-[#3D2331]/5 text-[#59414E] border-[#EADBCE]",
    dot: "bg-[#7E6875]",
  },
  planning: {
    badge: "bg-[#F4B942]/15 text-[#9C6D08] border-[#F4B942]/40 shadow-sm",
    dot: "bg-[#F4B942]",
    ping: true,
  },
  researching: {
    badge: "bg-[#3D2331]/10 text-[#3D2331] border-[#3D2331]/25 shadow-sm",
    dot: "bg-[#523143]",
    ping: true,
  },
  executing: {
    badge: "bg-[#087F5B]/10 text-[#087F5B] border-[#087F5B]/30 shadow-sm",
    dot: "bg-[#087F5B]",
    ping: true,
  },
  reflecting: {
    badge: "bg-[#E76F51]/15 text-[#C84F33] border-[#E76F51]/35 shadow-sm",
    dot: "bg-[#E76F51]",
    ping: true,
  },
  awaiting_approval: {
    badge: "bg-[#F4B942]/20 text-[#9C6D08] border-[#F4B942]/50 shadow-sm",
    dot: "bg-[#F4B942]",
    ping: true,
  },
  rejected: {
    badge: "bg-[#3D2331]/10 text-[#59414E] border-[#3D2331]/20",
    dot: "bg-[#7E6875]",
  },
  completed: {
    badge: "bg-[#087F5B]/15 text-[#066649] border-[#087F5B]/35 shadow-sm",
    dot: "bg-[#087F5B]",
  },
  failed: {
    badge: "bg-[#E76F51]/15 text-[#C84F33] border-[#E76F51]/35 shadow-sm",
    dot: "bg-[#E76F51]",
  },
};

const DEFAULT_CONFIG: StyleConfig = {
  badge: "bg-[#3D2331]/5 text-[#59414E] border-[#EADBCE]",
  dot: "bg-[#7E6875]",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const s = (status || "pending").toLowerCase();
  const config = STATUS_CONFIG[s] || DEFAULT_CONFIG;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border uppercase tracking-wider backdrop-blur-sm ${config.badge}`}
    >
      <span className="relative flex h-2 w-2">
        {config.ping && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${config.dot}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dot}`} />
      </span>
      {s.replaceAll("_", " ")}
    </span>
  );
}
