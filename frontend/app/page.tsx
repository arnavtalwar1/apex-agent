"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import TaskList from "@/components/TaskList";
import { api, getToken } from "@/lib/api";
import type { Task } from "@/types";
import { motion } from "framer-motion";
import {
  Sparkles,
  Terminal,
  RotateCcw,
  CheckCircle2,
  Loader2,
  Search,
  Cpu,
  Compass,
  Activity,
  Flame,
} from "lucide-react";

const TEMPLATE_PROMPTS = [
  {
    title: "Repository Architecture Analysis",
    prompt: "Investigate https://github.com/arnavtalwar1/apex-agent and synthesize an executive architecture deliverable.",
  },
  {
    title: "Algorithmic Runtime Benchmark",
    prompt: "Write a high-performance Python script to compute prime factorizations up to 100,000 and calculate throughput.",
  },
  {
    title: "Microservices Trade-off Analysis",
    prompt: "Analyze the architectural trade-offs between monolithic and event-driven microservices architectures.",
  },
];

export default function Dashboard() {
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
      if (statusFilter === "completed") return t.status.toLowerCase() === "completed";
      if (statusFilter === "failed") return t.status.toLowerCase() === "failed";
      if (statusFilter === "running") {
        return ["planning", "researching", "executing", "reflecting"].includes(t.status.toLowerCase());
      }
      return true;
    });
  }, [tasks, searchQuery, statusFilter]);

  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status.toLowerCase() === "completed").length;
  const totalReflections = tasks.reduce((acc, t) => acc + (t.reflection_count || 0), 0);
  const successRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 100;

  return (
    <div className="min-h-screen pb-16 bg-[#F7F3E8]">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        {/* Hero & Bento Metric Grid */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
        >
          {/* Main Hero Banner */}
          <div className="md:col-span-2 rounded-3xl border border-[#EADBCE] bg-gradient-to-br from-white via-[#FCFAF4] to-[#F7F3E8] p-8 flex flex-col justify-between relative overflow-hidden backdrop-blur-xl shadow-sm">
            <div className="absolute top-0 right-0 -mr-10 -mt-10 h-48 w-48 rounded-full bg-[#F4B942]/10 blur-3xl pointer-events-none" />
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-[#F4B942]/40 bg-[#F4B942]/15 px-3 py-1 text-xs font-bold text-[#3D2331] mb-4">
                <Sparkles size={14} className="text-[#D49520]" />
                <span>Autonomous Agentic Orchestration</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#3D2331] mb-2 leading-tight">
                Self-Improving Multi-Agent <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#087F5B] via-[#D49520] to-[#E76F51]">
                  Cognitive Workflows
                </span>
              </h1>
              <p className="text-sm text-[#59414E] max-w-md leading-relaxed mt-2 font-medium">
                Deploy autonomous AI workflows with automatic subtask decomposition, live web intelligence, Python sandbox execution, and reflection loops.
              </p>
            </div>

            <div className="mt-6 flex items-center gap-4 text-xs font-semibold text-[#59414E]">
              <span className="flex items-center gap-1.5">
                <Cpu size={14} className="text-[#087F5B]" /> Multi-Tier LLM Fallback
              </span>
              <span className="flex items-center gap-1.5">
                <Compass size={14} className="text-[#E76F51]" /> Live Web Grounding
              </span>
            </div>
          </div>

          {/* Metric 1: Success Rate */}
          <div className="rounded-3xl border border-[#EADBCE] bg-white/90 backdrop-blur-md p-6 flex flex-col justify-between relative overflow-hidden shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#59414E]">
                Cognitive Success
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#087F5B]/10 text-[#087F5B] border border-[#087F5B]/20">
                <CheckCircle2 size={18} />
              </div>
            </div>

            <div className="my-4">
              <div className="text-4xl font-extrabold text-[#3D2331] tracking-tight">
                {successRate}%
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-[#EADBCE] overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#087F5B] to-[#20C997] transition-all duration-1000"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>

            <p className="text-xs text-[#7E6875]">
              {completedTasks} completed out of {totalTasks} total operations
            </p>
          </div>

          {/* Metric 2: Self-Healing Reflections */}
          <div className="rounded-3xl border border-[#EADBCE] bg-white/90 backdrop-blur-md p-6 flex flex-col justify-between relative overflow-hidden shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#59414E]">
                Self-Healing Loops
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#E76F51]/10 text-[#E76F51] border border-[#E76F51]/20">
                <RotateCcw size={18} />
              </div>
            </div>

            <div className="my-4">
              <div className="text-4xl font-extrabold text-[#3D2331] tracking-tight">
                {totalReflections}
              </div>
              <div className="text-xs text-[#C84F33] font-semibold mt-1 flex items-center gap-1">
                <Activity size={12} /> Autonomous self-healing activations
              </div>
            </div>

            <p className="text-xs text-[#7E6875]">
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
          <div className="rounded-3xl border border-[#EADBCE] bg-white/95 backdrop-blur-xl p-6 shadow-md">
            <form onSubmit={handleCreateTask} className="relative">
              <label htmlFor="task-goal-input" className="sr-only">
                Task Objective
              </label>
              <div className="relative flex items-center">
                <div className="absolute left-5 text-[#D49520] pointer-events-none">
                  <Sparkles size={22} />
                </div>
                <input
                  id="task-goal-input"
                  type="text"
                  autoComplete="off"
                  aria-label="Task objective"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="What would you like APEX to plan, research, or execute today?..."
                  className="w-full rounded-2xl border border-[#EADBCE] bg-[#F7F3E8]/40 py-4 pl-14 pr-44 text-sm sm:text-base text-[#3D2331] placeholder-[#7E6875] focus:border-[#087F5B] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#087F5B]/10 transition-all shadow-inner"
                />
                <div className="absolute right-2">
                  <button
                    type="submit"
                    aria-label="Deploy Agent"
                    disabled={submitting || !goal.trim()}
                    className="flex items-center gap-2 rounded-xl bg-[#087F5B] hover:bg-[#066649] px-6 py-3 text-xs sm:text-sm font-bold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-[1.02] active:scale-[0.98]"
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
            <div className="mt-4 flex flex-wrap items-center gap-2 pt-2 border-t border-[#EADBCE]/80">
              <span className="text-xs font-semibold text-[#59414E] flex items-center gap-1">
                <Flame size={13} className="text-[#E76F51]" /> Suggestions:
              </span>
              {TEMPLATE_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  aria-label={`Use template: ${item.title}`}
                  onClick={() => setGoal(item.prompt)}
                  className="rounded-full border border-[#EADBCE] bg-white hover:bg-[#F7F3E8] hover:border-[#087F5B] hover:text-[#087F5B] px-3.5 py-1 text-xs text-[#59414E] transition-colors shadow-2xs font-medium"
                >
                  {item.title}
                </button>
              ))}
            </div>

            {error && (
              <div className="mt-4 rounded-xl border border-[#E76F51]/30 bg-[#E76F51]/10 px-4 py-2.5 text-xs text-[#C84F33] font-medium flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#E76F51] animate-pulse" />
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
              <h2 className="text-xl font-bold tracking-tight text-[#3D2331]">Operations Hub</h2>
              <span className="rounded-full bg-white border border-[#EADBCE] px-2.5 py-0.5 text-xs font-semibold text-[#59414E]">
                {filteredTasks.length} {filteredTasks.length === 1 ? "task" : "tasks"}
              </span>
            </div>

            {/* Filter Tabs & Search Bar */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Status Tabs */}
              <div className="flex items-center rounded-xl bg-white p-1 border border-[#EADBCE] text-xs font-semibold text-[#59414E]">
                {(["all", "running", "completed", "failed"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    aria-label={`Filter tasks by ${tab} status`}
                    onClick={() => setStatusFilter(tab)}
                    className={`rounded-lg px-3 py-1.5 capitalize transition-all ${
                      statusFilter === tab
                        ? "bg-[#087F5B] text-white shadow-sm"
                        : "hover:text-[#3D2331]"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div className="relative">
                <label htmlFor="task-search-input" className="sr-only">
                  Search Operations
                </label>
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7E6875]" />
                <input
                  id="task-search-input"
                  type="text"
                  autoComplete="off"
                  aria-label="Filter tasks by title or goal"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter tasks..."
                  className="rounded-xl border border-[#EADBCE] bg-white pl-8 pr-3 py-1.5 text-xs text-[#3D2331] placeholder-[#7E6875] focus:outline-none focus:border-[#087F5B] transition-colors"
                />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="rounded-3xl border border-[#EADBCE] bg-white/70 backdrop-blur-md p-20 text-center flex flex-col items-center justify-center shadow-sm">
              <Loader2 size={36} className="text-[#087F5B] animate-spin mb-3" />
              <p className="text-sm font-medium text-[#59414E]">Syncing cognitive operations...</p>
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
