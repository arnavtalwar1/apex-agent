import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full border-t border-[#EADBCE] bg-[#F7F3E8]/80 py-6 px-4 sm:px-6 text-xs text-[#7E6875]">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="font-extrabold tracking-wider text-[#3D2331]">ΛPEX</span>
          <span>&copy; {new Date().getFullYear()} APEX Agent.</span>
          <span className="hidden sm:inline">&bull;</span>
          <span className="hidden sm:inline">Rooted in knowledge. Rising to intelligence.</span>
        </div>

        <div className="flex items-center gap-6 font-medium">
          <Link
            href="/privacy"
            className="hover:text-[#3D2331] transition-colors underline flex items-center gap-1.5"
          >
            <ShieldCheck size={14} className="text-[#087F5B]" />
            Privacy Policy & GDPR
          </Link>
          <a
            href="https://github.com/arnavtalwar1/apex-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#3D2331] transition-colors"
          >
            Source
          </a>
        </div>
      </div>
    </footer>
  );
}
