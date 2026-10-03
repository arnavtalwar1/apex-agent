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
    badge: "bg-slate-900/80 text-slate-300 border-slate-700/60",
    dot: "bg-slate-400",
  },
  planning: {
    badge: "bg-amber-950/40 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-500/10",
    dot: "bg-amber-400",
    ping: true,
  },
  researching: {
    badge: "bg-purple-950/40 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/10",
    dot: "bg-purple-400",
    ping: true,
  },
  executing: {
    badge: "bg-indigo-950/40 text-indigo-300 border-indigo-500/40 shadow-sm shadow-indigo-500/10",
    dot: "bg-indigo-400",
    ping: true,
  },
  reflecting: {
    badge: "bg-rose-950/40 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-500/10",
    dot: "bg-rose-400",
    ping: true,
  },
  awaiting_approval: {
    badge: "bg-amber-950/60 text-amber-300 border-amber-500/60 shadow-sm shadow-amber-500/20",
    dot: "bg-amber-400",
    ping: true,
  },
  rejected: {
    badge: "bg-zinc-900 text-zinc-400 border-zinc-700/60",
    dot: "bg-zinc-500",
  },
  completed: {
    badge: "bg-emerald-950/40 text-emerald-300 border-emerald-500/40 shadow-sm shadow-emerald-500/10",
    dot: "bg-emerald-400",
  },
  failed: {
    badge: "bg-red-950/40 text-red-300 border-red-500/40 shadow-sm shadow-red-500/10",
    dot: "bg-red-400",
  },
};

const DEFAULT_CONFIG: StyleConfig = {
  badge: "bg-slate-900/80 text-slate-300 border-slate-700/60",
  dot: "bg-slate-400",
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
      {s}
    </span>
  );
}
