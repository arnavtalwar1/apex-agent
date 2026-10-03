"use client";

import React from "react";
import { 
  Sparkles, 
  GitFork, 
  Globe, 
  Terminal, 
  RotateCcw, 
  CheckCircle2, 
  Loader2,
  AlertCircle
} from "lucide-react";
import { motion } from "framer-motion";

interface PipelineStepperProps {
  currentNode?: string | null;
  status: string;
  reflectionCount?: number;
}

const NODES = [
  {
    id: "supervisor",
    label: "Supervisor",
    desc: "Goal Decomposition & Routing",
    icon: Sparkles,
    color: "from-blue-500 to-indigo-500",
  },
  {
    id: "planner",
    label: "Planner",
    desc: "Strategy Formulation",
    icon: GitFork,
    color: "from-amber-500 to-orange-500",
  },
  {
    id: "researcher",
    label: "Researcher",
    desc: "Web Intelligence & Search",
    icon: Globe,
    color: "from-purple-500 to-fuchsia-500",
  },
  {
    id: "executor",
    label: "Executor",
    desc: "Sandbox Runtime Execution",
    icon: Terminal,
    color: "from-emerald-500 to-teal-500",
  },
  {
    id: "reflector",
    label: "Reflector",
    desc: "Self-Critique & Validation",
    icon: RotateCcw,
    color: "from-rose-500 to-pink-500",
  },
];

export default function PipelineStepper({
  currentNode,
  status,
  reflectionCount = 0,
}: PipelineStepperProps) {
  const normStatus = (status || "").toLowerCase();
  const isCompleted = normStatus === "completed";
  const isFailed = normStatus === "failed";
  const activeNodeId = (currentNode || "").toLowerCase();

  // Find index of currently active node
  const activeIndex = NODES.findIndex((n) => n.id === activeNodeId);

  return (
    <div className="w-full rounded-2xl border border-white/10 bg-[#0d1424]/80 backdrop-blur-md p-6 shadow-xl mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-white/5 pb-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              {!isCompleted && !isFailed && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isCompleted ? "bg-emerald-400" : isFailed ? "bg-rose-500" : "bg-indigo-400"}`}></span>
            </span>
            Cognitive Pipeline Architecture
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            5-Stage Multi-Agent Orchestration with Automated Self-Correction
          </p>
        </div>

        {reflectionCount > 0 && (
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-950/40 px-3 py-1 text-xs font-semibold text-purple-300">
            <RotateCcw size={12} className="animate-spin text-purple-400" />
            <span>Self-Healing Loops: {reflectionCount}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
        {NODES.map((node, index) => {
          const Icon = node.icon;
          const isParallelActive = activeNodeId === "parallel" && (node.id === "planner" || node.id === "researcher");
          const isNodeFailed = isFailed && (activeNodeId === node.id || (activeIndex === -1 && index === 0));
          const isActive = (activeNodeId === node.id || isParallelActive) && !isCompleted && !isFailed;
          const isPassed = isCompleted || (activeIndex > -1 && index < activeIndex);

          return (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className={`relative flex flex-col items-center text-center p-4 rounded-xl border transition-all ${
                isNodeFailed
                  ? "border-rose-500/50 bg-rose-950/20 shadow-lg shadow-rose-500/10 ring-1 ring-rose-500/30 text-rose-300"
                  : isActive
                  ? "border-indigo-400/80 bg-indigo-950/30 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-400/50"
                  : isPassed
                  ? "border-emerald-500/30 bg-emerald-950/10 text-slate-300"
                  : "border-white/5 bg-white/[0.02] text-slate-500"
              }`}
            >
              {/* Node Icon Box */}
              <div
                className={`relative mb-3 flex h-12 w-12 items-center justify-center rounded-xl transition-transform ${
                  isNodeFailed
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/40 scale-105"
                    : isActive
                    ? "bg-gradient-to-br " + node.color + " text-white shadow-md shadow-indigo-500/30 scale-105"
                    : isPassed
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : "bg-slate-800/80 text-slate-400 border border-white/5"
                }`}
              >
                {isNodeFailed ? (
                  <AlertCircle size={22} className="text-rose-400" />
                ) : isActive ? (
                  <Loader2 size={22} className="animate-spin" />
                ) : isPassed ? (
                  <CheckCircle2 size={22} className="text-emerald-400" />
                ) : (
                  <Icon size={20} />
                )}
              </div>

              <div className="text-xs font-bold uppercase tracking-wider text-slate-200">
                {node.label}
              </div>

              <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">
                {isParallelActive ? "Concurrent Parallel Execution" : node.desc}
              </div>

              {isNodeFailed && (
                <span className="mt-2 text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                  FAILED
                </span>
              )}

              {isActive && (
                <span className="mt-2 text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20 animate-pulse">
                  {isParallelActive ? "CONCURRENT" : "EXECUTING"}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
