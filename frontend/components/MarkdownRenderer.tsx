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
      <div key={key} className="my-6 w-full overflow-x-auto rounded-2xl border border-[#EADBCE] bg-white shadow-xs">
        <table className="w-full text-left text-sm text-[#3D2331]">
          {tableHeader.length > 0 && (
            <thead className="border-b border-[#EADBCE] bg-[#F7F3E8] text-xs font-bold uppercase tracking-wider text-[#3D2331]">
              <tr>
                {tableHeader.map((th, idx) => (
                  <th key={idx} className="px-5 py-3.5 font-bold">
                    {parseInline(th)}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="divide-y divide-[#EADBCE]/60">
            {tableRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-[#F7F3E8]/40 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-5 py-3.5 text-[#3D2331]">
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
        <h4 key={`h4-${i}`} className="mt-5 mb-2 text-base font-bold text-[#3D2331]">
          {parseInline(line.slice(5))}
        </h4>
      );
      continue;
    }
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={`h3-${i}`} className="mt-6 mb-3 text-lg font-extrabold text-[#3D2331] flex items-center gap-2">
          <span className="w-1.5 h-4 bg-[#087F5B] rounded-full inline-block"></span>
          {parseInline(line.slice(4))}
        </h3>
      );
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={`h2-${i}`} className="mt-8 mb-4 text-xl font-extrabold text-[#3D2331] tracking-tight border-b border-[#EADBCE] pb-2 flex items-center gap-2">
          {parseInline(line.slice(3))}
        </h2>
      );
      continue;
    }
    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={`h1-${i}`} className="mt-8 mb-4 text-2xl font-black text-[#3D2331] tracking-tight">
          {parseInline(line.slice(2))}
        </h1>
      );
      continue;
    }

    // Horizontal Rule
    if (/^(\*\*\*|---|___)$/.test(trimmed)) {
      elements.push(<hr key={`hr-${i}`} className="my-6 border-[#EADBCE]" />);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={`bq-${i}`} className="my-4 border-l-4 border-[#087F5B] bg-[#F7F3E8] pl-4 py-2.5 italic text-[#59414E] rounded-r-xl">
          {parseInline(line.slice(2))}
        </blockquote>
      );
      continue;
    }

    // Unordered List item
    if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <div key={`li-${i}`} className="my-1.5 flex items-start gap-3 pl-2">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#087F5B]" />
          <span className="text-[#3D2331] leading-relaxed text-sm">{parseInline(line.slice(2))}</span>
        </div>
      );
      continue;
    }

    // Ordered List item
    const matchOrdered = line.match(/^(\d+)\.\s+(.*)$/);
    if (matchOrdered) {
      elements.push(
        <div key={`oli-${i}`} className="my-1.5 flex items-start gap-3 pl-2">
          <span className="font-mono text-xs font-bold text-[#087F5B] shrink-0 mt-0.5">
            {matchOrdered[1]}.
          </span>
          <span className="text-[#3D2331] leading-relaxed text-sm">{parseInline(matchOrdered[2])}</span>
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
      <p key={`p-${i}`} className="my-2.5 text-sm leading-relaxed text-[#3D2331]">
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
          className="rounded-md bg-[#F7F3E8] border border-[#EADBCE] px-1.5 py-0.5 font-mono text-xs text-[#087F5B] font-semibold"
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
              <strong key={bIdx} className="font-bold text-[#3D2331]">
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
    <div className="my-5 overflow-hidden rounded-2xl border border-[#3D2331]/20 bg-[#251520] shadow-xl text-white">
      <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-[#F4B942]" />
          <span className="font-mono text-xs font-semibold uppercase text-[#EADBCE]">
            {language || "code"}
          </span>
        </div>
        <button
          type="button"
          aria-label="Copy code to clipboard"
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium text-[#EADBCE] hover:bg-white/10 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check size={14} className="text-[#087F5B]" />
              <span className="text-[#087F5B]">Copied</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-[#F7F3E8]">
        <code>{code}</code>
      </pre>
    </div>
  );
}
