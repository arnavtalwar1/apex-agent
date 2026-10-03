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
    color: "from-[#3D2331] to-[#523143]",
  },
  {
    id: "planner",
    label: "Planner",
    desc: "Strategy Formulation",
    icon: GitFork,
    color: "from-[#D49520] to-[#F4B942]",
  },
  {
    id: "researcher",
    label: "Researcher",
    desc: "Web Intelligence & Search",
    icon: Globe,
    color: "from-[#087F5B] to-[#20C997]",
  },
  {
    id: "executor",
    label: "Executor",
    desc: "Sandbox Runtime Execution",
    icon: Terminal,
    color: "from-[#066649] to-[#087F5B]",
  },
  {
    id: "reflector",
    label: "Reflector",
    desc: "Self-Critique & Validation",
    icon: RotateCcw,
    color: "from-[#E76F51] to-[#F4A261]",
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
    <div className="w-full rounded-2xl border border-[#EADBCE] bg-white/80 backdrop-blur-md p-6 shadow-sm mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-[#EADBCE]/80 pb-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#3D2331] flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              {!isCompleted && !isFailed && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#087F5B] opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isCompleted ? "bg-[#087F5B]" : isFailed ? "bg-[#E76F51]" : "bg-[#F4B942]"}`}></span>
            </span>
            Cognitive Pipeline Architecture
          </h3>
          <p className="text-xs text-[#59414E] mt-0.5">
            5-Stage Autonomous Multi-Agent Orchestration with Automated Self-Correction
          </p>
        </div>

        {reflectionCount > 0 && (
          <div className="inline-flex items-center gap-2 rounded-full border border-[#E76F51]/30 bg-[#E76F51]/10 px-3 py-1 text-xs font-semibold text-[#C84F33]">
            <RotateCcw size={12} className="animate-spin text-[#E76F51]" />
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
                  ? "border-[#E76F51]/50 bg-[#E76F51]/10 text-[#C84F33]"
                  : isActive
                  ? "border-[#087F5B] bg-[#087F5B]/10 shadow-md shadow-[#087F5B]/10 ring-2 ring-[#087F5B]/20 text-[#3D2331]"
                  : isPassed
                  ? "border-[#087F5B]/30 bg-[#087F5B]/5 text-[#3D2331]"
                  : "border-[#EADBCE] bg-[#F7F3E8]/40 text-[#7E6875]"
              }`}
            >
              {/* Node Icon Box */}
              <div
                className={`relative mb-3 flex h-12 w-12 items-center justify-center rounded-xl transition-transform ${
                  isNodeFailed
                    ? "bg-[#E76F51]/20 text-[#E76F51] border border-[#E76F51]/40 scale-105"
                    : isActive
                    ? "bg-gradient-to-br " + node.color + " text-white shadow-md shadow-[#087F5B]/20 scale-105"
                    : isPassed
                    ? "bg-[#087F5B]/15 text-[#087F5B] border border-[#087F5B]/30"
                    : "bg-white text-[#7E6875] border border-[#EADBCE]"
                }`}
              >
                {isNodeFailed ? (
                  <AlertCircle size={22} className="text-[#E76F51]" />
                ) : isActive ? (
                  <Loader2 size={22} className="animate-spin text-white" />
                ) : isPassed ? (
                  <CheckCircle2 size={22} className="text-[#087F5B]" />
                ) : (
                  <Icon size={20} />
                )}
              </div>

              <div className="text-xs font-bold uppercase tracking-wider text-[#3D2331]">
                {node.label}
              </div>

              <div className="text-[11px] text-[#59414E] mt-1 line-clamp-1">
                {isParallelActive ? "Concurrent Parallel Execution" : node.desc}
              </div>

              {isNodeFailed && (
                <span className="mt-2 text-[10px] font-bold text-[#C84F33] bg-[#E76F51]/15 px-2 py-0.5 rounded-full border border-[#E76F51]/30">
                  FAILED
                </span>
              )}

              {isActive && (
                <span className="mt-2 text-[10px] font-bold text-[#066649] bg-[#087F5B]/15 px-2 py-0.5 rounded-full border border-[#087F5B]/30 animate-pulse">
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
