"use client";

import { FormEvent, useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import TaskList from "@/components/TaskList";
import { api, getToken } from "@/lib/api";
import type { Task } from "@/types";
import { motion } from "framer-motion";
import { 
  Sparkles, 
  Terminal, 
  Activity, 
  CheckCircle2, 
  Loader2, 
  Search, 
  RotateCcw, 
  Cpu, 
  Compass, 
  Flame 
} from "lucide-react";

const TEMPLATE_PROMPTS = [
  {
    title: "🚗 EV Market Pricing & Range 2026",
    prompt: "Provide a comprehensive market analysis of 2026 electric vehicle models, MSRP pricing, range, battery capacity, and key market trends in a structured comparison table.",
  },
  {
    title: "🔒 FastAPI Security & Auth Audit",
    prompt: "Perform a security audit checklist for a FastAPI production application covering JWT authentication, rate limiting, CORS configuration, and SQL injection prevention.",
  },
  {
    title: "⚡ High-Throughput Async Scraper",
    prompt: "Design and implement a high-throughput asynchronous Python scraper architecture with rate-limiting, proxy rotation, and retry backoff using httpx and asyncio.",
  },
  {
    title: "📊 Semiconductor Supply Chain Forecast",
    prompt: "Research and analyze global semiconductor manufacturing trends, TSMC 2nm process milestones, and AI accelerator GPU supply forecasts through 2027.",
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goal, setGoal] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    const fetchTasks = async () => {
      try {
        const fetchedTasks = await api.listTasks();
        setTasks(fetchedTasks);
      } catch (err) {
        console.error("Failed to load tasks", err);
        setError("Unable to load tasks. Please try signing in again.");
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [router]);

  const handleCreateTask = async (e: FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setSubmitting(true);
    setError("");

    try {
      const newTask = await api.createTask(goal.trim());
      setTasks((prev) => [newTask, ...prev]);
      setGoal("");
      router.push(`/tasks/${newTask.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task.");
      setSubmitting(false);
    }
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const matchesSearch =
        searchQuery.trim() === "" ||
        (t.title && t.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
        t.goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(t.id).includes(searchQuery);

      if (!matchesSearch) return false;

      if (statusFilter === "all") return true;
      if (statusFilter === "completed") return t.status?.toLowerCase() === "completed";
      if (statusFilter === "failed") return t.status?.toLowerCase() === "failed";
      if (statusFilter === "running") {
        const s = t.status?.toLowerCase();
        return s === "planning" || s === "researching" || s === "executing" || s === "reflecting";
      }
      return true;
    });
  }, [tasks, searchQuery, statusFilter]);

  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status?.toLowerCase() === "completed").length;
  const successRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 100;
  const totalReflections = tasks.reduce((acc, t) => acc + (t.reflection_count || 0), 0);

  return (
    <div className="min-h-screen pt-28 pb-16 px-4 sm:px-6">
      <Navbar />

      <main className="max-w-6xl mx-auto">
        {/* Hero & Bento Metric Grid */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
        >
          {/* Main Hero Banner */}
          <div className="md:col-span-2 rounded-3xl border border-white/10 bg-gradient-to-br from-[#101935]/90 via-[#0e162d]/80 to-[#0a0f1d]/90 p-8 flex flex-col justify-between relative overflow-hidden backdrop-blur-xl shadow-2xl">
            <div className="absolute top-0 right-0 -mr-10 -mt-10 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-950/60 px-3 py-1 text-xs font-semibold text-indigo-300 mb-4">
                <Sparkles size={14} className="text-indigo-400" />
                <span>Next-Gen Agentic Orchestration</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2 leading-tight">
                Self-Improving Multi-Agent <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-rose-400">
                  Cognitive Workflows
                </span>
              </h1>
              <p className="text-sm text-slate-300 max-w-md leading-relaxed mt-2">
                Deploy autonomous AI workflows with automatic subtask decomposition, live web intelligence, Python sandbox execution, and reflection loops.
              </p>
            </div>

            <div className="mt-6 flex items-center gap-4 text-xs font-semibold text-slate-400">
              <span className="flex items-center gap-1.5">
                <Cpu size={14} className="text-indigo-400" /> Multi-Tier LLM Fallback
              </span>
              <span className="flex items-center gap-1.5">
                <Compass size={14} className="text-rose-400" /> Live Web Grounding
              </span>
            </div>
          </div>

          {/* Metric 1: Success Rate */}
          <div className="rounded-3xl border border-white/10 bg-[#0d1527]/70 backdrop-blur-md p-6 flex flex-col justify-between relative overflow-hidden shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Cognitive Success
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 size={18} />
              </div>
            </div>

            <div className="my-4">
              <div className="text-4xl font-extrabold text-white tracking-tight">
                {successRate}%
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-1000"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>

            <p className="text-xs text-slate-400">
              {completedTasks} completed out of {totalTasks} total operations
            </p>
          </div>

          {/* Metric 2: Self-Healing Reflections */}
          <div className="rounded-3xl border border-white/10 bg-[#0d1527]/70 backdrop-blur-md p-6 flex flex-col justify-between relative overflow-hidden shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Self-Healing Loops
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <RotateCcw size={18} />
              </div>
            </div>

            <div className="my-4">
              <div className="text-4xl font-extrabold text-white tracking-tight">
                {totalReflections}
              </div>
              <div className="text-xs text-purple-300 font-semibold mt-1 flex items-center gap-1">
                <Activity size={12} /> Autonomous self-healing activations
              </div>
            </div>

            <p className="text-xs text-slate-400">
              Auto-critique & correction via Reflector Node
            </p>
          </div>
        </motion.div>

        {/* Omnibar & Agent Deployment */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className="mb-8"
        >
          <div className="rounded-3xl border border-white/10 bg-[#0c1322]/80 backdrop-blur-xl p-6 shadow-2xl">
            <form onSubmit={handleCreateTask} className="relative">
              <div className="relative flex items-center">
                <div className="absolute left-5 text-indigo-400 pointer-events-none">
                  <Sparkles size={22} />
                </div>
                <input
                  type="text"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="What would you like APEX to plan, research, or execute today?..."
                  className="w-full rounded-2xl border border-white/10 bg-white/[0.03] py-4 pl-14 pr-44 text-sm sm:text-base text-white placeholder-slate-500 focus:border-indigo-500 focus:bg-white/[0.05] focus:outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all shadow-inner"
                />
                <div className="absolute right-2">
                  <button
                    type="submit"
                    disabled={submitting || !goal.trim()}
                    className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-rose-500 hover:from-indigo-500 hover:to-rose-400 px-6 py-3 text-xs sm:text-sm font-bold text-white shadow-lg shadow-indigo-500/25 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98]"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="animate-spin" size={16} />
                        <span>Deploying...</span>
                      </>
                    ) : (
                      <>
                        <Terminal size={16} />
                        <span>Deploy Agent</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>

            {/* Prompt Template Chips */}
            <div className="mt-4 flex flex-wrap items-center gap-2 pt-2 border-t border-white/5">
              <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                <Flame size={13} className="text-rose-400" /> Suggestions:
              </span>
              {TEMPLATE_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setGoal(item.prompt)}
                  className="rounded-full border border-white/5 bg-white/[0.02] hover:bg-white/[0.08] hover:border-indigo-500/40 px-3 py-1 text-xs text-slate-300 transition-colors"
                >
                  {item.title}
                </button>
              ))}
            </div>

            {error && (
              <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-950/30 px-4 py-2.5 text-xs text-rose-300 font-medium flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                {error}
              </div>
            )}
          </div>
        </motion.div>

        {/* Task Operations List Header & Filter Controls */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 px-1">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold tracking-tight text-white">Operations Hub</h2>
              <span className="rounded-full bg-white/5 border border-white/5 px-2.5 py-0.5 text-xs font-semibold text-slate-400">
                {filteredTasks.length} {filteredTasks.length === 1 ? "task" : "tasks"}
              </span>
            </div>

            {/* Filter Tabs & Search Bar */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Status Tabs */}
              <div className="flex items-center rounded-xl bg-white/[0.04] p-1 border border-white/5 text-xs font-semibold text-slate-400">
                {(["all", "running", "completed", "failed"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setStatusFilter(tab)}
                    className={`rounded-lg px-3 py-1.5 capitalize transition-all ${
                      statusFilter === tab
                        ? "bg-indigo-600 text-white shadow-sm"
                        : "hover:text-white"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter tasks..."
                  className="rounded-xl border border-white/5 bg-white/[0.03] pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="rounded-3xl border border-white/5 bg-[#0d1527]/40 backdrop-blur-md p-20 text-center flex flex-col items-center justify-center">
              <Loader2 size={36} className="text-indigo-400 animate-spin mb-3" />
              <p className="text-sm font-medium text-slate-400">Syncing cognitive operations...</p>
            </div>
          ) : (
            <TaskList
              tasks={filteredTasks}
              onTaskDeleted={(deletedId) => setTasks((prev) => prev.filter((t) => t.id !== deletedId))}
            />
          )}
        </motion.div>
      </main>
    </div>
  );
}
