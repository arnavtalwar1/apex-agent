"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import PipelineStepper from "@/components/PipelineStepper";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { api, getToken } from "@/lib/api";
import type { AgentLogEntry, Task } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Play,
  RotateCcw,
  CheckCircle2,
  Terminal,
  Sparkles,
  Copy,
  Check,
  Download,
  FileText,
  Code2,
  Trash2,
  Filter,
  ArrowDownCircle,
  AlertCircle,
} from "lucide-react";

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = Number(params.id);

  const [task, setTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"deliverable" | "plan" | "terminal" | "raw">("deliverable");
  const [copied, setCopied] = useState(false);
  const [terminalFilter, setTerminalFilter] = useState<string>("all");
  const [autoScroll, setAutoScroll] = useState(true);

  const logContainerRef = useRef<HTMLDivElement>(null);
  const cancelStreamRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, running, autoScroll]);

  useEffect(() => {
    return () => {
      if (cancelStreamRef.current) {
        cancelStreamRef.current();
      }
    };
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    if (!taskId) return;

    const fetchTask = async () => {
      try {
        const fetchedTask = await api.getTask(taskId);
        setTask(fetchedTask);

        // Auto-select tab based on availability
        if (fetchedTask.final_output) {
          setActiveTab("deliverable");
        } else if (fetchedTask.plan) {
          setActiveTab("plan");
        } else {
          setActiveTab("terminal");
        }
      } catch (err) {
        console.error("Failed to load task", err);
        setError("Unable to load task details.");
      } finally {
        setLoading(false);
      }
    };

    fetchTask();
  }, [taskId, router]);

  const parseEventToLog = (event: Record<string, unknown>): AgentLogEntry | null => {
    const timestamp = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    if ("error" in event && typeof event.error === "string") {
      return { timestamp, agent: "reflector", message: `Error detected: ${event.error}` };
    }
    if ("status" in event && event.status === "completed") {
      return { timestamp, agent: "supervisor", message: "Workflow execution completed successfully." };
    }

    for (const [key, value] of Object.entries(event)) {
      const agentName = key.toLowerCase();
      const val = value as Record<string, unknown>;
      if (!val || typeof val !== "object") continue;

      if (agentName === "supervisor") {
        const nextNode = val.next_node as string;
        return {
          timestamp,
          agent: "supervisor",
          message: nextNode
            ? `Supervisor evaluated state → Delegating to [${nextNode.toUpperCase()}]`
            : "Supervisor active.",
        };
      }
      if (agentName === "planner") {
        const planText = typeof val.plan === "string" ? val.plan : JSON.stringify(val);
        return { timestamp, agent: "planner", message: `Formulated Execution Plan:\n${planText}` };
      }
      if (agentName === "researcher") {
        const researchText = typeof val.research_data === "string" ? val.research_data : JSON.stringify(val);
        return { timestamp, agent: "researcher", message: `Live Intelligence Gathering:\n${researchText}` };
      }
      if (agentName === "executor") {
        const resultText = typeof val.execution_result === "string" ? val.execution_result : JSON.stringify(val);
        return { timestamp, agent: "executor", message: `Executed in Sandbox Runtime:\n${resultText}` };
      }
      if (agentName === "reflector") {
        const critique = typeof val.reflection_critique === "string" ? val.reflection_critique : "";
        const plan = typeof val.plan === "string" ? val.plan : "";
        return {
          timestamp,
          agent: "reflector",
          message: `Self-Correction & Reflection Loop:\nCritique: ${critique}\nAdapted Plan: ${plan}`,
        };
      }
    }
    return null;
  };

  const handleRunAgent = () => {
    if (running) return;

    setRunning(true);
    setError("");
    setLogs([]);
    setActiveTab("terminal");

    cancelStreamRef.current = api.runTask(
      taskId,
      (eventData) => {
        const entry = parseEventToLog(eventData);
        if (entry) {
          setLogs((prev) => [...prev, entry]);
        }
      },
      async () => {
        setRunning(false);
        try {
          const updated = await api.getTask(taskId);
          setTask(updated);
          if (updated.final_output) {
            setActiveTab("deliverable");
          }
        } catch (err) {
          console.error("Error refreshing task state", err);
        }
      },
      (err) => {
        setRunning(false);
        setError(err.message || "Agent execution failed");
      }
    );
  };

  const effectiveDeliverable = useMemo(() => {
    if (!task) return "";
    const raw = (task.final_output || "").trim();
    const isTrivial =
      !raw ||
      raw.toLowerCase().includes("no output") ||
      raw === "SUCCESS:" ||
      raw === "SUCCESS" ||
      (raw.startsWith("SUCCESS:") && raw.length < 50) ||
      raw.startsWith("FAILED (code");

    if (isTrivial && task.plan) {
      const badge = raw.startsWith("SUCCESS")
        ? "\n\n---\n✅ **Sandbox Verification:** Execution verified successfully (exit code 0)."
        : raw.startsWith("FAILED")
        ? `\n\n---\n### 🧪 Sandbox Verification Note\n\`\`\`\n${raw}\n\`\`\``
        : "";
      return `${task.plan}${badge}`;
    }
    return task.final_output || "";
  }, [task]);

  const handleCopyOutput = async () => {
    if (!effectiveDeliverable) return;
    try {
      await navigator.clipboard.writeText(effectiveDeliverable);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Failed to copy", e);
    }
  };

  const handleExportMarkdown = () => {
    if (!effectiveDeliverable || !task) return;
    const blob = new Blob([effectiveDeliverable], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `APEX-Task-${task.id}-Deliverable.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredLogs = useMemo(() => {
    if (terminalFilter === "all") return logs;
    return logs.filter((l) => l.agent.toLowerCase() === terminalFilter.toLowerCase());
  }, [logs, terminalFilter]);

  const getAgentBadge = (agent: string) => {
    const a = agent.toLowerCase();
    switch (a) {
      case "supervisor":
        return (
          <span className="rounded-md bg-blue-950/80 text-blue-300 border border-blue-500/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Supervisor
          </span>
        );
      case "planner":
        return (
          <span className="rounded-md bg-amber-950/80 text-amber-300 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Planner
          </span>
        );
      case "researcher":
        return (
          <span className="rounded-md bg-purple-950/80 text-purple-300 border border-purple-500/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Researcher
          </span>
        );
      case "executor":
        return (
          <span className="rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Executor
          </span>
        );
      case "reflector":
        return (
          <span className="rounded-md bg-rose-950/80 text-rose-300 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Reflector
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-slate-800 text-slate-300 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            {agent}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pb-16">
        <Navbar />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 text-center flex flex-col items-center justify-center pt-24 text-slate-400">
          <RotateCcw size={40} className="animate-spin mb-4 text-indigo-400" />
          <p className="font-semibold text-slate-300">Synchronizing Cognitive State...</p>
        </main>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen pb-16">
        <Navbar />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 text-center pt-20">
          <p className="text-xl font-bold text-white mb-4">Task not found</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-indigo-400 font-bold hover:underline"
          >
            <ArrowLeft size={18} /> Return to Operations Dashboard
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        {/* Breadcrumb Navigation */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={14} /> Back to Operations
          </Link>
        </motion.div>

        {/* Task Objective Card */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-white/10 bg-[#0d1527]/80 backdrop-blur-xl p-6 sm:p-8 shadow-2xl mb-8 relative overflow-hidden"
        >
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2.5 mb-3">
                <StatusBadge status={task.status} />
                <span className="font-mono text-xs font-bold text-slate-400 bg-white/5 px-2.5 py-0.5 rounded-full border border-white/5">
                  ID #{task.id}
                </span>
                {task.reflection_count > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-purple-300 bg-purple-950/60 px-2.5 py-0.5 rounded-full border border-purple-500/30">
                    <RotateCcw size={12} className="text-purple-400" />
                    {task.reflection_count} {task.reflection_count === 1 ? "reflection" : "reflections"}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-3">
                {task.title || "Autonomous Task Execution"}
              </h1>

              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 text-sm text-slate-300 leading-relaxed font-medium">
                {task.goal}
              </div>
            </div>

            {/* Run Action Button */}
            <div className="shrink-0 flex flex-col items-center sm:items-end gap-3">
              <button
                type="button"
                onClick={handleRunAgent}
                disabled={running}
                className="w-full sm:w-auto rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-rose-500 hover:from-indigo-500 hover:to-rose-400 px-8 py-4 text-sm font-extrabold text-white shadow-xl shadow-indigo-500/25 disabled:opacity-50 transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-3"
              >
                {running ? (
                  <>
                    <RotateCcw className="animate-spin" size={18} />
                    <span>Executing Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Play size={18} className="fill-current" />
                    <span>{task.final_output ? "Re-Run Pipeline" : "Initialize Agent"}</span>
                  </>
                )}
              </button>

              {error && (
                <div className="text-xs text-rose-400 font-medium flex items-center gap-2 bg-rose-950/50 px-3 py-1.5 rounded-full border border-rose-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                  {error}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Cognitive Pipeline Architecture Stepper */}
        <PipelineStepper
          currentNode={task.current_node}
          status={task.status}
          reflectionCount={task.reflection_count}
        />

        {/* Tab Switcher & Quick Actions Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          {/* Tabs */}
          <div className="flex items-center rounded-2xl bg-white/[0.04] p-1.5 border border-white/5">
            <button
              type="button"
              onClick={() => setActiveTab("deliverable")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "deliverable"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <FileText size={14} />
              <span>Final Deliverable</span>
              {effectiveDeliverable && (
                <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block" />
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("plan")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "plan"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Sparkles size={14} />
              <span>Strategic Plan</span>
              {task.plan && <span className="h-2 w-2 rounded-full bg-amber-400 inline-block" />}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("terminal")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "terminal"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Terminal size={14} />
              <span>Terminal Stream</span>
              {logs.length > 0 && (
                <span className="rounded-full bg-white/10 px-1.5 py-0.2 text-[10px]">
                  {logs.length}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("raw")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "raw"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Code2 size={14} />
              <span>State JSON</span>
            </button>
          </div>

          {/* Quick Actions (when deliverable exists) */}
          {effectiveDeliverable && activeTab === "deliverable" && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopyOutput}
                className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-2 text-xs font-bold text-slate-200 transition-colors"
              >
                {copied ? (
                  <>
                    <Check size={14} className="text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy Text</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleExportMarkdown}
                className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-2 text-xs font-bold text-slate-200 transition-colors"
              >
                <Download size={14} />
                <span>Export Markdown</span>
              </button>
            </div>
          )}
        </div>

        {/* Tab Content Display */}
        <AnimatePresence mode="wait">
          {activeTab === "deliverable" && (
            <motion.div
              key="deliverable"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`rounded-3xl border bg-[#0d1628]/90 backdrop-blur-xl p-8 shadow-2xl relative ${
                task.status === "failed" ? "border-rose-500/25" : "border-emerald-500/20"
              }`}
            >
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                    task.status === "failed"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  }`}
                >
                  {task.status === "failed" ? <AlertCircle size={22} /> : <CheckCircle2 size={22} />}
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {task.status === "failed" ? "Execution Deliverable (Verification Alert)" : "Executive Deliverable & Output"}
                  </h2>
                  <p className="text-xs text-slate-400">
                    {task.status === "failed"
                      ? "Execution encountered an error. Click 'Re-Run Pipeline' above to trigger self-healing automated execution."
                      : "Compiled and verified by the APEX multi-agent execution pipeline"}
                  </p>
                </div>
              </div>

              {task.status === "failed" && (
                <div className="mb-6 rounded-2xl border border-rose-500/30 bg-rose-950/30 p-4 text-xs text-rose-300 flex items-start gap-3">
                  <AlertCircle size={18} className="shrink-0 text-rose-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-bold text-rose-200">Execution Notice</p>
                    <p className="mt-1 text-slate-300 leading-relaxed">
                      Sandbox execution returned an error during this run. Click the <span className="font-semibold text-white">Re-Run Pipeline</span> button above to trigger the self-healing reflection loop and verify code execution.
                    </p>
                  </div>
                </div>
              )}

              {effectiveDeliverable ? (
                <div className="text-slate-200">
                  <MarkdownRenderer content={effectiveDeliverable} />
                </div>
              ) : (
                <div className="py-16 text-center text-slate-400 flex flex-col items-center">
                  <Terminal size={40} className="text-slate-600 mb-3" />
                  <p className="font-semibold text-slate-300">Deliverable not yet generated</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm">
                    Click &quot;Initialize Agent&quot; above to run the pipeline and generate the final output.
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === "plan" && (
            <motion.div
              key="plan"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-3xl border border-amber-500/20 bg-[#0d1628]/90 backdrop-blur-xl p-8 shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Sparkles size={22} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Strategic Execution Plan</h2>
                  <p className="text-xs text-slate-400">
                    Cognitive goal decomposition and step-by-step strategy formulated by Planner Node
                  </p>
                </div>
              </div>

              {task.plan ? (
                <div className="text-slate-200">
                  <MarkdownRenderer content={task.plan} />
                </div>
              ) : (
                <div className="py-16 text-center text-slate-400 flex flex-col items-center">
                  <Sparkles size={40} className="text-slate-600 mb-3" />
                  <p className="font-semibold text-slate-300">No execution plan available yet</p>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === "terminal" && (
            <motion.div
              key="terminal"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-3xl border border-white/10 bg-[#090d18] shadow-2xl overflow-hidden"
            >
              {/* Terminal Window Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-white/10 bg-white/[0.02]">
                <div className="flex items-center gap-3">
                  <div className="flex gap-2">
                    <span className="h-3 w-3 rounded-full bg-rose-500/80" />
                    <span className="h-3 w-3 rounded-full bg-amber-400/80" />
                    <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-300 ml-2 flex items-center gap-2">
                    <Terminal size={14} className="text-indigo-400" />
                    APEX Terminal Stream
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Agent Role Filter */}
                  <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 text-[11px] font-semibold text-slate-400">
                    <Filter size={12} className="ml-1 mr-1 text-slate-500" />
                    {["all", "supervisor", "planner", "researcher", "executor", "reflector"].map(
                      (role) => (
                        <button
                          key={role}
                          type="button"
                          onClick={() => setTerminalFilter(role)}
                          className={`rounded-lg px-2 py-0.5 capitalize transition-colors ${
                            terminalFilter === role
                              ? "bg-indigo-600 text-white"
                              : "hover:text-white"
                          }`}
                        >
                          {role}
                        </button>
                      )
                    )}
                  </div>

                  {/* Auto-scroll toggle */}
                  <button
                    type="button"
                    onClick={() => setAutoScroll(!autoScroll)}
                    className={`flex items-center gap-1 rounded-xl px-2.5 py-1 text-xs font-semibold border transition-colors ${
                      autoScroll
                        ? "border-indigo-500/40 bg-indigo-950/50 text-indigo-300"
                        : "border-white/10 bg-white/5 text-slate-400"
                    }`}
                  >
                    <ArrowDownCircle size={13} />
                    <span>Auto-Scroll</span>
                  </button>
                </div>
              </div>

              {/* Terminal Logs Container */}
              <div
                ref={logContainerRef}
                className="h-[520px] overflow-y-auto p-6 font-mono text-xs text-slate-300 space-y-4 leading-relaxed"
              >
                {filteredLogs.length === 0 && !running && (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500">
                    <Terminal size={48} className="mb-3 opacity-30 text-indigo-400" />
                    <p className="font-sans text-sm font-medium text-slate-400">
                      Terminal stream idle.
                    </p>
                    <p className="font-sans text-xs text-slate-600 mt-1">
                      Click &quot;Initialize Agent&quot; to inspect real-time multi-agent communication.
                    </p>
                  </div>
                )}

                {filteredLogs.map((log, index) => (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    key={index}
                    className="flex flex-col sm:flex-row sm:items-start gap-3 border-b border-white/5 pb-4 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center gap-2 shrink-0 sm:w-48">
                      <span className="text-slate-500 text-[11px]">{log.timestamp}</span>
                      {getAgentBadge(log.agent)}
                    </div>
                    <div className="flex-1 whitespace-pre-wrap break-words leading-relaxed text-slate-200">
                      {log.message}
                    </div>
                  </motion.div>
                ))}

                {running && (
                  <div className="flex items-center gap-3 text-indigo-400 animate-pulse pt-3 text-xs font-bold font-mono">
                    <RotateCcw size={14} className="animate-spin" />
                    <span>COGNITIVE ENGINE WORKING (STREAMING EVENT TOKENS)...</span>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === "raw" && (
            <motion.div
              key="raw"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="rounded-3xl border border-white/10 bg-[#090d18] p-6 shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
                <span className="font-mono text-xs font-bold text-slate-400">
                  APEX Internal State Inspector
                </span>
                <span className="text-xs text-slate-500">FastAPI SQLite Model</span>
              </div>
              <pre className="overflow-x-auto p-4 rounded-xl bg-black/40 font-mono text-xs text-emerald-400 leading-relaxed">
                {JSON.stringify(task, null, 2)}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
