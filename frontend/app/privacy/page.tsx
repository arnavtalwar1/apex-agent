import type { Metadata } from "next";
import Link from "next/link";
import ApexLogo from "@/components/ApexLogo";
import { ArrowLeft, CheckCircle2, Cookie, Database, Lock, ShieldCheck, UserCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "Privacy Policy & GDPR Compliance | APEX Agent",
  description: "Comprehensive privacy policy, GDPR compliance disclosure, and data governance practices for the APEX Agent platform.",
};

export default function PrivacyPolicyPage() {
  const lastUpdated = "October 5, 2026";

  return (
    <div className="min-h-screen bg-[#F7F3E8] text-[#3D2331] py-12 px-4 sm:px-6 lg:px-8 selection:bg-[#F4B942]/30 selection:text-[#3D2331]">
      <div className="max-w-4xl mx-auto">
        {/* Navigation & Header */}
        <div className="mb-8 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-[#59414E] hover:text-[#3D2331] bg-white border border-[#EADBCE] px-3 py-1.5 rounded-xl shadow-xs transition-colors"
          >
            <ArrowLeft size={14} />
            Back to Dashboard
          </Link>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#087F5B]/10 text-[#087F5B] border border-[#087F5B]/20">
              <ShieldCheck size={13} />
              GDPR & PCI DSS Compliant
            </span>
          </div>
        </div>

        {/* Hero Card */}
        <div className="rounded-3xl border border-[#EADBCE] bg-white/80 backdrop-blur-md p-8 sm:p-10 shadow-sm mb-10">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-14 w-14 rounded-2xl bg-white border border-[#EADBCE] flex items-center justify-center shadow-xs">
              <ApexLogo variant="navbar" size={40} />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#3D2331]">
                Privacy Policy & Data Protection
              </h1>
              <p className="text-xs font-medium text-[#7E6875] mt-1">
                Last updated: {lastUpdated} &bull; Version 1.2
              </p>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-[#59414E]">
            APEX Agent (&ldquo;we&rdquo;, &ldquo;our&rdquo;, or &ldquo;platform&rdquo;) values your privacy and is committed to protecting your personal data in accordance with the <strong>General Data Protection Regulation (GDPR) (EU) 2016/679</strong>, the <strong>Data Protection Act 2018 (UK GDPR)</strong>, and international security standards including <strong>PCI DSS v4.0</strong>. This policy outlines how information is collected, processed, and safeguarded when using APEX.
          </p>
        </div>

        {/* Policy Sections */}
        <div className="space-y-8">
          {/* 1. Controller & Principles */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-9 w-9 rounded-xl bg-[#087F5B]/10 text-[#087F5B] flex items-center justify-center">
                <ShieldCheck size={18} />
              </div>
              <h2 className="text-lg font-bold text-[#3D2331]">1. Data Controller & Core Principles</h2>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-[#59414E]">
              <p>
                The data controller for information processed through this application is the operator of the APEX platform. We adhere strictly to the fundamental principles of Article 5 of the GDPR:
              </p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li><strong>Lawfulness, fairness, and transparency:</strong> We only process data required to execute your requested AI tasks.</li>
                <li><strong>Purpose limitation:</strong> User inputs are strictly processed for task reasoning and synthesis, never sold or shared with advertisers.</li>
                <li><strong>Data minimization:</strong> We collect only necessary identifiers (email, hashed credentials, task goals).</li>
                <li><strong>Storage limitation:</strong> Users can permanently delete tasks and associated traces at any time via the dashboard.</li>
                <li><strong>Integrity and confidentiality:</strong> Data in transit is protected with TLS 1.3 encryption and HSTS.</li>
              </ul>
            </div>
          </section>

          {/* 2. Information We Collect & Lawful Basis */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-9 w-9 rounded-xl bg-[#F4B942]/20 text-[#3D2331] flex items-center justify-center">
                <Database size={18} />
              </div>
              <h2 className="text-lg font-bold text-[#3D2331]">2. Data Collected & Legal Basis (GDPR Art. 6)</h2>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-[#59414E]">
              <p>We process the following categories of data:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                <div className="p-4 rounded-xl bg-[#F7F3E8] border border-[#EADBCE]">
                  <h3 className="font-bold text-[#3D2331] mb-1">Account & Authentication</h3>
                  <p>Email address and cryptographically hashed passwords (using bcrypt with work factor 12). Used exclusively for authentication under <em>GDPR Art. 6(1)(b) (Contract Performance)</em>.</p>
                </div>
                <div className="p-4 rounded-xl bg-[#F7F3E8] border border-[#EADBCE]">
                  <h3 className="font-bold text-[#3D2331] mb-1">Task Operations & Code</h3>
                  <p>User-submitted task prompts, synthesized deliverables, and execution logs. Processed under <em>GDPR Art. 6(1)(b)</em> to deliver requested AI operations.</p>
                </div>
              </div>
            </div>
          </section>

          {/* 3. Cookies & Tracking Disclosure */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-9 w-9 rounded-xl bg-[#087F5B]/10 text-[#087F5B] flex items-center justify-center">
                <Cookie size={18} />
              </div>
              <h2 className="text-lg font-bold text-[#3D2331]">3. Zero Cookies & Zero Third-Party Trackers</h2>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-[#59414E]">
              <p>
                <strong>APEX does not use tracking cookies, marketing cookies, or third-party analytics scripts.</strong>
              </p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li>We do not set profiling or advertising cookies.</li>
                <li>Authentication utilizes modern standard JSON Web Tokens (JWT) stored in client session storage, strictly scoped to user authentication.</li>
                <li>Because no non-essential cookies or tracking technologies are employed, no cookie consent banner is legally required under the EU ePrivacy Directive (Directive 2002/58/EC).</li>
              </ul>
            </div>
          </section>

          {/* 4. Security & PCI DSS 6.4 Compliance */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-9 w-9 rounded-xl bg-[#3D2331] text-[#F7F3E8] flex items-center justify-center">
                <Lock size={18} />
              </div>
              <h2 className="text-lg font-bold text-[#3D2331]">4. Technical Security & PCI DSS Requirement 6.4</h2>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-[#59414E]">
              <p>
                In alignment with <strong>PCI DSS v4.0 Requirement 6.4</strong> and <strong>GDPR Article 32</strong>, APEX employs industry-grade security countermeasures against client-side tampering, script injection, and clickjacking:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-3 rounded-xl border border-[#EADBCE] bg-white">
                  <span className="font-bold text-[#3D2331] block">Content-Security-Policy</span>
                  <span className="text-[11px] text-[#7E6875]">Strict resource restriction preventing unauthorized script injection.</span>
                </div>
                <div className="p-3 rounded-xl border border-[#EADBCE] bg-white">
                  <span className="font-bold text-[#3D2331] block">X-Frame-Options: DENY</span>
                  <span className="text-[11px] text-[#7E6875]">Prevents iframe embedding and clickjacking attacks.</span>
                </div>
                <div className="p-3 rounded-xl border border-[#EADBCE] bg-white">
                  <span className="font-bold text-[#3D2331] block">X-Content-Type-Options</span>
                  <span className="text-[11px] text-[#7E6875]">Blocks MIME-sniffing vulnerabilities across all responses.</span>
                </div>
              </div>
            </div>
          </section>

          {/* 5. Your Rights Under GDPR */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-9 w-9 rounded-xl bg-[#087F5B]/10 text-[#087F5B] flex items-center justify-center">
                <UserCheck size={18} />
              </div>
              <h2 className="text-lg font-bold text-[#3D2331]">5. Your Rights as a Data Subject</h2>
            </div>
            <div className="space-y-3 text-xs leading-relaxed text-[#59414E]">
              <p>Under GDPR Articles 15 through 22, you possess clear rights regarding your personal data:</p>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <CheckCircle2 size={14} className="text-[#087F5B] mt-0.5 shrink-0" />
                  <span><strong>Right to Access & Rectification (Arts. 15, 16):</strong> Review your account details and profile at any time.</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 size={14} className="text-[#087F5B] mt-0.5 shrink-0" />
                  <span><strong>Right to Erasure / &ldquo;Right to be Forgotten&rdquo; (Art. 17):</strong> Delete your task data and execution records directly using the delete action in the dashboard, which cascades immediately across records.</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 size={14} className="text-[#087F5B] mt-0.5 shrink-0" />
                  <span><strong>Right to Data Portability (Art. 20):</strong> Export task outputs and plans through the standard JSON API endpoints.</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 size={14} className="text-[#087F5B] mt-0.5 shrink-0" />
                  <span><strong>Right to Lodge a Complaint:</strong> You have the right to lodge a complaint with your local EU/EEA data protection supervisory authority.</span>
                </div>
              </div>
            </div>
          </section>

          {/* 6. Contact & Data Officer */}
          <section className="rounded-2xl border border-[#EADBCE] bg-white p-6 sm:p-8 shadow-xs">
            <h2 className="text-lg font-bold text-[#3D2331] mb-2">6. Contact & Privacy Inquiries</h2>
            <p className="text-xs leading-relaxed text-[#59414E]">
              For any questions regarding this Privacy Policy, data subject access requests, or to exercise your GDPR rights, please open an inquiry on our official GitHub repository:{" "}
              <a
                href="https://github.com/arnavtalwar1/apex-agent/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#087F5B] font-semibold underline hover:text-[#066145]"
              >
                github.com/arnavtalwar1/apex-agent
              </a>
              .
            </p>
          </section>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-[#EADBCE] flex flex-col sm:flex-row items-center justify-between text-xs text-[#7E6875] gap-3">
          <span>&copy; {new Date().getFullYear()} APEX Agent. All rights reserved.</span>
          <div className="flex items-center gap-4">
            <Link href="/" className="hover:text-[#3D2331] underline">
              Dashboard
            </Link>
            <Link href="/login" className="hover:text-[#3D2331] underline">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
