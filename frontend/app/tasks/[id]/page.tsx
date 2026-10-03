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
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

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
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push(`/login?redirect=${encodeURIComponent(`/tasks/${taskId}`)}`);
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
        let msg = "Supervisor active.";
        if (nextNode) {
          msg = nextNode.toLowerCase() === "parallel"
            ? "Supervisor initiated simultaneous parallel execution → [PLANNER] & [RESEARCHER] working concurrently"
            : `Supervisor evaluated state → Delegating to [${nextNode.toUpperCase()}]`;
        }
        return {
          timestamp,
          agent: "supervisor",
          message: msg,
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
    setTask((prev) => (prev ? { ...prev, current_node: "supervisor", status: "running" } : prev));

    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
    }
    // Background polling fallback every 2.5 seconds to guarantee UI updates even if SSE buffers
    pollTimerRef.current = setInterval(async () => {
      try {
        const latest = await api.getTask(taskId);
        setTask((prev) => (prev ? { ...prev, ...latest } : latest));
      } catch (err) {
        console.warn("Task state background poll note", err);
      }
    }, 2500);

    const cleanup = () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };

    cancelStreamRef.current = api.runTask(
      taskId,
      (eventData) => {
        const entry = parseEventToLog(eventData);
        if (entry) {
          setLogs((prev) => [...prev, entry]);
        }

        // Real-time Stepper & Task State Sync
        setTask((prev) => {
          if (!prev) return prev;
          const next = { ...prev };
          if (eventData.status && typeof eventData.status === "string") {
            next.status = eventData.status;
          }
          if ("supervisor" in eventData && typeof eventData.supervisor === "object") {
            const sup = eventData.supervisor as Record<string, unknown>;
            if (sup?.next_node) {
              next.current_node = String(sup.next_node).toLowerCase();
            }
          }
          if ("planner" in eventData && typeof eventData.planner === "object") {
            next.current_node = "planner";
            const p = eventData.planner as Record<string, unknown>;
            if (p?.plan && typeof p.plan === "string") next.plan = p.plan;
          }
          if ("researcher" in eventData) {
            next.current_node = "researcher";
          }
          if ("executor" in eventData && typeof eventData.executor === "object") {
            next.current_node = "executor";
            const e = eventData.executor as Record<string, unknown>;
            if (e?.execution_result && typeof e.execution_result === "string") {
              next.final_output = e.execution_result;
            }
          }
          if ("reflector" in eventData) {
            next.current_node = "reflector";
            next.reflection_count = (next.reflection_count || 0) + 1;
          }
          return next;
        });
      },
      async () => {
        cleanup();
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
        cleanup();
        setRunning(false);
        setError(err.message || "Agent execution failed");
      }
    );
  };

  const effectiveDeliverable = useMemo(() => {
    if (!task) return "";
    return (task.final_output || "").trim();
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
          <span className="rounded-md bg-[#3D2331] text-[#F7F3E8] border border-[#59414E] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Supervisor
          </span>
        );
      case "planner":
        return (
          <span className="rounded-md bg-[#F4B942]/20 text-[#F4B942] border border-[#F4B942]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Planner
          </span>
        );
      case "researcher":
        return (
          <span className="rounded-md bg-[#087F5B]/20 text-[#087F5B] border border-[#087F5B]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Researcher
          </span>
        );
      case "executor":
        return (
          <span className="rounded-md bg-[#087F5B]/20 text-[#087F5B] border border-[#087F5B]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Executor
          </span>
        );
      case "reflector":
        return (
          <span className="rounded-md bg-[#E76F51]/20 text-[#E76F51] border border-[#E76F51]/30 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            Reflector
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-[#3D2331]/10 text-[#3D2331] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider">
            {agent}
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pb-16 bg-[#F7F3E8]">
        <Navbar />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 text-center flex flex-col items-center justify-center pt-24 text-[#59414E]">
          <RotateCcw size={40} className="animate-spin mb-4 text-[#087F5B]" />
          <p className="font-semibold text-[#3D2331]">Synchronizing Cognitive State...</p>
        </main>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen pb-16 bg-[#F7F3E8]">
        <Navbar />
        <main className="max-w-6xl mx-auto px-4 sm:px-6 text-center pt-20">
          <p className="text-xl font-bold text-[#3D2331] mb-4">Task not found</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-[#087F5B] font-bold hover:underline"
          >
            <ArrowLeft size={18} /> Return to Operations Dashboard
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20 bg-[#F7F3E8]">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        {/* Breadcrumb Navigation */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-bold text-[#59414E] hover:text-[#3D2331] transition-colors"
          >
            <ArrowLeft size={14} /> Back to Operations
          </Link>
        </motion.div>

        {/* Task Objective Card */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-[#EADBCE] bg-white/90 backdrop-blur-xl p-6 sm:p-8 shadow-sm mb-8 relative overflow-hidden"
        >
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2.5 mb-3">
                <StatusBadge status={task.status} />
                <span className="font-mono text-xs font-bold text-[#59414E] bg-[#F7F3E8] px-2.5 py-0.5 rounded-full border border-[#EADBCE]">
                  ID #{task.id}
                </span>
                {task.reflection_count > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-[#E76F51] bg-[#E76F51]/10 px-2.5 py-0.5 rounded-full border border-[#E76F51]/30">
                    <RotateCcw size={12} className="text-[#E76F51]" />
                    {task.reflection_count} {task.reflection_count === 1 ? "reflection" : "reflections"}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#3D2331] mb-3">
                {task.title || "Autonomous Task Execution"}
              </h1>

              <div className="rounded-2xl border border-[#EADBCE] bg-[#F7F3E8]/50 p-4 text-sm text-[#59414E] leading-relaxed font-medium">
                {task.goal}
              </div>
            </div>

            {/* Run Action Button */}
            <div className="shrink-0 flex flex-col items-center sm:items-end gap-3">
              <button
                type="button"
                onClick={handleRunAgent}
                disabled={running}
                aria-label={task.final_output ? "Re-Run Pipeline" : "Initialize Agent"}
                className="w-full sm:w-auto rounded-2xl bg-[#087F5B] hover:bg-[#066649] px-8 py-4 text-sm font-extrabold text-white shadow-lg shadow-[#087F5B]/20 disabled:opacity-50 transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-3"
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
                <div className="text-xs text-[#E76F51] font-medium flex items-center gap-2 bg-[#E76F51]/10 px-3 py-1.5 rounded-full border border-[#E76F51]/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E76F51] animate-pulse" />
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
          <div role="tablist" aria-label="Task content views" className="flex items-center rounded-2xl bg-white p-1.5 border border-[#EADBCE] shadow-2xs">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "deliverable"}
              aria-label="Final Deliverable"
              onClick={() => setActiveTab("deliverable")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "deliverable"
                  ? "bg-[#087F5B] text-white shadow-md shadow-[#087F5B]/20"
                  : "text-[#59414E] hover:text-[#3D2331]"
              }`}
            >
              <FileText size={14} />
              <span>Final Deliverable</span>
              {effectiveDeliverable && (
                <span className="h-2 w-2 rounded-full bg-[#F4B942] inline-block" />
              )}
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "plan"}
              aria-label="Strategic Plan"
              onClick={() => setActiveTab("plan")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "plan"
                  ? "bg-[#087F5B] text-white shadow-md shadow-[#087F5B]/20"
                  : "text-[#59414E] hover:text-[#3D2331]"
              }`}
            >
              <Sparkles size={14} />
              <span>Strategic Plan</span>
              {task.plan && <span className="h-2 w-2 rounded-full bg-[#F4B942] inline-block" />}
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "terminal"}
              aria-label="Terminal Stream"
              onClick={() => setActiveTab("terminal")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "terminal"
                  ? "bg-[#087F5B] text-white shadow-md shadow-[#087F5B]/20"
                  : "text-[#59414E] hover:text-[#3D2331]"
              }`}
            >
              <Terminal size={14} />
              <span>Terminal Stream</span>
              {logs.length > 0 && (
                <span className="rounded-full bg-white/20 px-1.5 py-0.2 text-[10px]">
                  {logs.length}
                </span>
              )}
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "raw"}
              aria-label="State JSON Inspector"
              onClick={() => setActiveTab("raw")}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${
                activeTab === "raw"
                  ? "bg-[#087F5B] text-white shadow-md shadow-[#087F5B]/20"
                  : "text-[#59414E] hover:text-[#3D2331]"
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
                aria-label="Copy deliverable text to clipboard"
                onClick={handleCopyOutput}
                className="flex items-center gap-2 rounded-xl border border-[#EADBCE] bg-white hover:bg-[#F7F3E8] px-4 py-2 text-xs font-bold text-[#3D2331] transition-colors shadow-2xs"
              >
                {copied ? (
                  <>
                    <Check size={14} className="text-[#087F5B]" />
                    <span className="text-[#087F5B]">Copied</span>
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
                aria-label="Export deliverable as Markdown"
                onClick={handleExportMarkdown}
                className="flex items-center gap-2 rounded-xl border border-[#EADBCE] bg-white hover:bg-[#F7F3E8] px-4 py-2 text-xs font-bold text-[#3D2331] transition-colors shadow-2xs"
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
              className={`rounded-3xl border bg-white p-8 sm:p-10 shadow-sm relative ${
                task.status === "failed" ? "border-[#E76F51]/30" : "border-[#EADBCE]"
              }`}
            >
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#EADBCE]">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                    task.status === "failed"
                      ? "bg-[#E76F51]/10 text-[#E76F51] border-[#E76F51]/20"
                      : "bg-[#087F5B]/10 text-[#087F5B] border-[#087F5B]/20"
                  }`}
                >
                  {task.status === "failed" ? <AlertCircle size={22} /> : <CheckCircle2 size={22} />}
                </div>
                <div>
                  <h2 className="text-lg font-bold text-[#3D2331]">
                    {task.status === "failed" ? "Execution Failure & Diagnostic Error" : "Executive Deliverable & Output"}
                  </h2>
                  <p className="text-xs text-[#59414E]">
                    {task.status === "failed"
                      ? "The pipeline encountered an error and did not generate a successful deliverable. See error details below."
                      : "Compiled and verified by the APEX multi-agent execution pipeline"}
                  </p>
                </div>
              </div>

              {task.status === "failed" && (
                <div className="mb-6 rounded-2xl border border-[#E76F51]/30 bg-[#E76F51]/10 p-4 text-xs text-[#C84F33] flex items-start gap-3">
                  <AlertCircle size={18} className="shrink-0 text-[#E76F51] mt-0.5" />
                  <div className="flex-1">
                    <p className="font-bold text-[#C84F33]">Execution Error</p>
                    <p className="mt-1 text-[#59414E] leading-relaxed">
                      Execution failed. Click the <span className="font-semibold text-[#3D2331]">Re-Run Pipeline</span> button above to re-trigger execution or view logs in the Terminal Stream.
                    </p>
                  </div>
                </div>
              )}

              {effectiveDeliverable ? (
                <div className="text-[#3D2331]">
                  <MarkdownRenderer content={effectiveDeliverable} />
                </div>
              ) : task.status === "failed" ? (
                <div className="py-16 text-center text-[#59414E] flex flex-col items-center">
                  <AlertCircle size={40} className="text-[#E76F51] mb-3" />
                  <p className="font-semibold text-[#E76F51]">Execution failed without deliverable</p>
                  <p className="text-xs text-[#7E6875] mt-1 max-w-sm">
                    No answer or deliverable could be produced for this task.
                  </p>
                </div>
              ) : (
                <div className="py-16 text-center text-[#59414E] flex flex-col items-center">
                  <Terminal size={40} className="text-[#7E6875] mb-3" />
                  <p className="font-semibold text-[#3D2331]">Deliverable not yet generated</p>
                  <p className="text-xs text-[#7E6875] mt-1 max-w-sm">
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
              className="rounded-3xl border border-[#EADBCE] bg-white p-8 sm:p-10 shadow-sm"
            >
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#EADBCE]">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F4B942]/15 text-[#D49520] border border-[#F4B942]/30">
                  <Sparkles size={22} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-[#3D2331]">Strategic Execution Plan</h2>
                  <p className="text-xs text-[#59414E]">
                    Cognitive goal decomposition and step-by-step strategy formulated by Planner Node
                  </p>
                </div>
              </div>

              {task.plan ? (
                <div className="text-[#3D2331]">
                  <MarkdownRenderer content={task.plan} />
                </div>
              ) : (
                <div className="py-16 text-center text-[#59414E] flex flex-col items-center">
                  <Sparkles size={40} className="text-[#7E6875] mb-3" />
                  <p className="font-semibold text-[#3D2331]">No execution plan available yet</p>
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
              className="rounded-3xl border border-[#3D2331]/20 bg-[#251520] shadow-xl overflow-hidden text-white"
            >
              {/* Terminal Window Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-3">
                  <div className="flex gap-2">
                    <span className="h-3 w-3 rounded-full bg-[#E76F51]" />
                    <span className="h-3 w-3 rounded-full bg-[#F4B942]" />
                    <span className="h-3 w-3 rounded-full bg-[#087F5B]" />
                  </div>
                  <span className="font-mono text-xs font-bold text-[#F7F3E8] ml-2 flex items-center gap-2">
                    <Terminal size={14} className="text-[#F4B942]" />
                    APEX Terminal Stream
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Agent Role Filter */}
                  <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 text-[11px] font-semibold text-[#EADBCE]">
                    <Filter size={12} className="ml-1 mr-1 text-[#EADBCE]/60" />
                    {["all", "supervisor", "planner", "researcher", "executor", "reflector"].map(
                      (role) => (
                        <button
                          key={role}
                          type="button"
                          aria-label={`Filter logs by ${role}`}
                          onClick={() => setTerminalFilter(role)}
                          className={`rounded-lg px-2 py-0.5 capitalize transition-colors ${
                            terminalFilter === role
                              ? "bg-[#087F5B] text-white"
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
                    aria-label={`Toggle auto-scroll, currently ${autoScroll ? "enabled" : "disabled"}`}
                    onClick={() => setAutoScroll(!autoScroll)}
                    className={`flex items-center gap-1 rounded-xl px-2.5 py-1 text-xs font-semibold border transition-colors ${
                      autoScroll
                        ? "border-[#087F5B]/50 bg-[#087F5B]/20 text-[#087F5B]"
                        : "border-white/10 bg-white/5 text-[#EADBCE]"
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
                className="h-[520px] overflow-y-auto p-6 font-mono text-xs text-[#EADBCE] space-y-4 leading-relaxed"
              >
                {filteredLogs.length === 0 && !running && (
                  <div className="h-full flex flex-col items-center justify-center text-[#7E6875]">
                    <Terminal size={48} className="mb-3 opacity-30 text-[#F4B942]" />
                    <p className="font-sans text-sm font-medium text-[#EADBCE]">
                      Terminal stream idle.
                    </p>
                    <p className="font-sans text-xs text-[#7E6875] mt-1">
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
                      <span className="text-[#EADBCE]/50 text-[11px]">{log.timestamp}</span>
                      {getAgentBadge(log.agent)}
                    </div>
                    <div className="flex-1 whitespace-pre-wrap break-words leading-relaxed text-[#F7F3E8]">
                      {log.message}
                    </div>
                  </motion.div>
                ))}

                {running && (
                  <div className="flex items-center gap-3 text-[#F4B942] animate-pulse pt-3 text-xs font-bold font-mono">
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
              className="rounded-3xl border border-[#3D2331]/20 bg-[#251520] p-6 shadow-xl overflow-hidden"
            >
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
                <span className="font-mono text-xs font-bold text-[#EADBCE]">
                  APEX Internal State Inspector
                </span>
                <span className="text-xs text-[#7E6875]">FastAPI SQLite Model</span>
              </div>
              <pre className="overflow-x-auto p-4 rounded-xl bg-black/30 font-mono text-xs text-[#087F5B] leading-relaxed">
                {JSON.stringify(task, null, 2)}
              </pre>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
