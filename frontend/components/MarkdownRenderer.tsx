"use client";

import React, { useState } from "react";
import { Check, Copy, Terminal } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  if (!content) return null;

  // Split into lines for structured block parsing
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeLanguage = "";
  let codeBuffer: string[] = [];

  let inTable = false;
  let tableHeader: string[] = [];
  let tableRows: string[][] = [];

  const flushCodeBlock = (key: string) => {
    if (codeBuffer.length === 0) return;
    const fullCode = codeBuffer.join("\n");
    elements.push(
      <CodeBlock key={key} language={codeLanguage} code={fullCode} />
    );
    codeBuffer = [];
    codeLanguage = "";
    inCodeBlock = false;
  };

  const flushTable = (key: string) => {
    if (tableHeader.length === 0 && tableRows.length === 0) return;
    elements.push(
      <div key={key} className="my-6 w-full overflow-x-auto rounded-xl border border-white/10 bg-[#0d1424] shadow-lg">
        <table className="w-full text-left text-sm text-slate-300">
          {tableHeader.length > 0 && (
            <thead className="border-b border-white/10 bg-white/5 text-xs font-semibold uppercase tracking-wider text-slate-200">
              <tr>
                {tableHeader.map((th, idx) => (
                  <th key={idx} className="px-5 py-3.5 font-bold">
                    {parseInline(th)}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="divide-y divide-white/5">
            {tableRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-white/[0.03] transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-5 py-3 text-slate-300">
                    {parseInline(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableHeader = [];
    tableRows = [];
    inTable = false;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block fences
    if (line.trim().startsWith("```")) {
      if (inCodeBlock) {
        flushCodeBlock(`code-${i}`);
      } else {
        if (inTable) flushTable(`table-${i}`);
        inCodeBlock = true;
        codeLanguage = line.trim().slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    // Markdown Table parsing
    const trimmed = line.trim();
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const cells = trimmed
        .slice(1, -1)
        .split("|")
        .map((c) => c.trim());

      // Check if separator line (| --- | --- |)
      const isSeparator = cells.every((c) => /^:?-+:?$/.test(c));
      if (isSeparator) {
        inTable = true;
        continue;
      }

      if (!inTable) {
        inTable = true;
        tableHeader = cells;
      } else {
        tableRows.push(cells);
      }
      continue;
    } else if (inTable) {
      flushTable(`table-${i}`);
    }

    // Headings
    if (line.startsWith("#### ")) {
      elements.push(
        <h4 key={`h4-${i}`} className="mt-5 mb-2 text-base font-semibold text-slate-200">
          {parseInline(line.slice(5))}
        </h4>
      );
      continue;
    }
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={`h3-${i}`} className="mt-6 mb-3 text-lg font-bold text-indigo-300 flex items-center gap-2">
          <span className="w-1.5 h-4 bg-indigo-500 rounded-full inline-block"></span>
          {parseInline(line.slice(4))}
        </h3>
      );
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={`h2-${i}`} className="mt-8 mb-4 text-xl font-bold text-white tracking-tight border-b border-white/10 pb-2 flex items-center gap-2">
          {parseInline(line.slice(3))}
        </h2>
      );
      continue;
    }
    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={`h1-${i}`} className="mt-8 mb-4 text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-200 to-indigo-400">
          {parseInline(line.slice(2))}
        </h1>
      );
      continue;
    }

    // Horizontal Rule
    if (/^(\*\*\*|---|___)$/.test(trimmed)) {
      elements.push(<hr key={`hr-${i}`} className="my-6 border-white/10" />);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={`bq-${i}`} className="my-4 border-l-4 border-indigo-500 bg-indigo-950/20 pl-4 py-2 italic text-slate-300 rounded-r-lg">
          {parseInline(line.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered List item
    if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <div key={`li-${i}`} className="my-1.5 flex items-start gap-3 pl-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
          <span className="text-slate-300 leading-relaxed text-sm">{parseInline(line.slice(2))}</span>
        </div>
      );
      continue;
    }

    // Ordered List item
    const matchOrdered = line.match(/^(\d+)\.\s+(.*)$/);
    if (matchOrdered) {
      elements.push(
        <div key={`oli-${i}`} className="my-1.5 flex items-start gap-3 pl-2">
          <span className="font-mono text-xs font-bold text-indigo-400 shrink-0 mt-0.5">
            {matchOrdered[1]}.
          </span>
          <span className="text-slate-300 leading-relaxed text-sm">{parseInline(matchOrdered[2])}</span>
        </div>
      );
      continue;
    }

    // Empty lines
    if (!trimmed) {
      elements.push(<div key={`empty-${i}`} className="h-2" />);
      continue;
    }

    // Standard paragraph
    elements.push(
      <p key={`p-${i}`} className="my-2 text-sm leading-relaxed text-slate-300">
        {parseInline(line)}
      </p>
    );
  }

  if (inCodeBlock) flushCodeBlock("code-end");
  if (inTable) flushTable("table-end");

  return <div className={`font-sans leading-normal ${className}`}>{elements}</div>;
}

// Inline parser for bold, italic, code, links
function parseInline(text: string): React.ReactNode {
  // Split by inline code first
  const parts = text.split(/(`[^`]+`)/g);

  return parts.map((part, idx) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={idx}
          className="rounded-md bg-indigo-950/70 border border-indigo-500/30 px-1.5 py-0.5 font-mono text-xs text-indigo-300 font-semibold"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Parse bold within regular text
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return (
      <React.Fragment key={idx}>
        {boldParts.map((bPart, bIdx) => {
          if (bPart.startsWith("**") && bPart.endsWith("**")) {
            return (
              <strong key={bIdx} className="font-semibold text-white">
                {bPart.slice(2, -2)}
              </strong>
            );
          }
          return bPart;
        })}
      </React.Fragment>
    );
  });
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Failed to copy code", e);
    }
  };

  return (
    <div className="my-5 overflow-hidden rounded-xl border border-white/10 bg-[#080d1a] shadow-xl">
      <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-indigo-400" />
          <span className="font-mono text-xs font-semibold uppercase text-slate-400">
            {language || "code"}
          </span>
        </div>
        <button
          type="button"
          aria-label="Copy code to clipboard"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check size={14} className="text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
        <code>{code}</code>
      </pre>
    </div>
  );
}
