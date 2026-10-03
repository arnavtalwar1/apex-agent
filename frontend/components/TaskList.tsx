"use client";

import { useRouter } from "next/navigation";
import type { Task } from "@/types";
import StatusBadge from "./StatusBadge";
import { motion } from "framer-motion";
import { ArrowUpRight, RotateCcw, Trash2, Calendar, FileText, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { useState } from "react";

interface TaskListProps {
  tasks: Task[];
  onTaskDeleted?: (id: number) => void;
}

export default function TaskList({ tasks, onTaskDeleted }: TaskListProps) {
  const router = useRouter();
  const [deletingId, setDeletingId] = useState<number | null>(null);

  if (!tasks || tasks.length === 0) {
    return (
      <div className="rounded-3xl border border-white/5 bg-[#0e1628]/40 backdrop-blur-md p-16 text-center text-slate-400">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-950/50 text-indigo-400 border border-indigo-500/20">
          <FileText size={28} />
        </div>
        <p className="text-base font-semibold text-slate-200">No operations found</p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Deploy an agent goal using the prompt input above to watch APEX plan, research, and execute.
        </p>
      </div>
    );
  }

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this task?")) return;

    setDeletingId(id);
    try {
      await api.deleteTask(id);
      if (onTaskDeleted) {
        onTaskDeleted(id);
      }
    } catch (err) {
      console.error("Failed to delete task", err);
      alert("Failed to delete task");
    } finally {
      setDeletingId(null);
    }
  };

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid gap-4 md:grid-cols-2"
    >
      {tasks.map((task) => {
        const hasDeliverable = Boolean(task.final_output);

        return (
          <motion.div
            variants={item}
            key={task.id}
            onClick={() => router.push(`/tasks/${task.id}`)}
            className="group cursor-pointer rounded-2xl border border-white/10 bg-[#0d1527]/70 backdrop-blur-md p-6 transition-all duration-300 hover:border-indigo-500/50 hover:bg-[#121c33]/90 hover:shadow-xl hover:shadow-indigo-500/10 hover:-translate-y-1 relative overflow-hidden flex flex-col justify-between"
          >
            {/* Ambient hover glow inside card */}
            <div className="absolute top-0 right-0 -mr-16 -mt-16 h-36 w-36 rounded-full bg-indigo-500/10 blur-2xl group-hover:bg-indigo-500/20 transition-all pointer-events-none" />

            <div className="relative z-10">
              {/* Card Header */}
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-2">
                  <StatusBadge status={task.status} />
                  <span className="font-mono text-xs font-semibold text-slate-500 bg-white/5 px-2 py-0.5 rounded-md border border-white/5">
                    #{task.id}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {task.reflection_count > 0 && (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-purple-300 bg-purple-950/60 px-2 py-0.5 rounded-full border border-purple-500/30">
                      <RotateCcw size={11} className="text-purple-400" />
                      {task.reflection_count}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={(e) => handleDelete(e, task.id)}
                    disabled={deletingId === task.id}
                    aria-label={`Delete task ${task.id}`}
                    className="h-8 w-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 hover:bg-rose-950/60 hover:text-rose-400 hover:border-rose-500/30 border border-transparent transition-all z-20"
                    title="Delete Operation"
                  >
                    <Trash2 size={14} />
                  </button>
                  <div className="h-8 w-8 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                    <ArrowUpRight size={16} />
                  </div>
                </div>
              </div>

              {/* Title & Goal */}
              <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1 mb-2">
                {task.title || task.goal.slice(0, 60)}
              </h3>

              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-4">
                {task.goal}
              </p>
            </div>

            {/* Footer */}
            <div className="relative z-10 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
              <div className="flex items-center gap-1.5">
                <Calendar size={12} className="text-slate-500" />
                <span>
                  {new Date(task.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>

              {hasDeliverable && (
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <CheckCircle2 size={12} />
                  Deliverable Ready
                </span>
              )}
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
