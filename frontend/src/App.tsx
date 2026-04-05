/**
 * Vulcan OmniPro 220 — Executable Knowledge Engine
 * Product-facing UI. No landing page. No demo mode. Straight to work.
 */

import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  ChevronDown,
  Gauge,
  Loader2,
  RotateCcw,
  Send,
  ShieldCheck,
  TriangleAlert,
  Zap,
  Settings,
  Key,
  CheckCircle2,
  X,
} from 'lucide-react';
import ArtifactRenderer from './components/ArtifactRenderer';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Message {
  role: 'user' | 'assistant';
  content: string;
  artifacts?: any[];
  images?: any[];
  technicalResponse?: {
    outcome?: { level: OutcomeLevel; headline: string; valid: boolean; reason: string };
    instruction?: string;
    consequences?: { label: string; text: string }[];
    constraint_trace?: { rule: string; passed: boolean; severity: string; detail: string }[];
    explanation: string;
    state: Record<string, any>;
    simulation: { step: number; event: string; effect: string }[];
    comparison?: Record<string, any>;
    confidence: { label: string; score: number };
    assumptions: string[];
    sources: { source: string; page: number; node_type: string; title?: string }[];
  };
}

interface QuickQuery {
  label: string;
  prompt: string;
  badge: string;
}

type OutcomeLevel = 'SAFE' | 'SUBOPTIMAL' | 'FAILURE RISK' | 'DAMAGE RISK' | 'INSUFFICIENT_STATE';

/* ------------------------------------------------------------------ */
/*  Quick queries — always visible above the input bar                  */
/* ------------------------------------------------------------------ */

const quickQueries: QuickQuery[] = [
  { label: 'Polarity', prompt: 'What happens if TIG polarity is reversed?', badge: 'FAILURE RISK' },
  { label: 'Duty cycle', prompt: "What's the duty cycle for MIG welding at 200A on 240V?", badge: 'SAFE' },
  { label: 'Defect', prompt: "I'm getting porosity in my flux-cored welds. What should I check?", badge: 'FAILURE RISK' },
  { label: 'Setup', prompt: 'What are the recommended settings for welding 1/4 inch mild steel?', badge: 'SAFE' },
];

/* ------------------------------------------------------------------ */
/*  App                                                                */
/* ------------------------------------------------------------------ */

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [apiKeyStatus, setApiKeyStatus] = useState<{ configured: boolean; provider: string } | null>(null);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [apiKeyProvider, setApiKeyProvider] = useState('openrouter');
  const [apiKeySaving, setApiKeySaving] = useState(false);
  const [apiKeyError, setApiKeyError] = useState('');
  const [apiKeySuccess, setApiKeySuccess] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    fetchStats();
    fetchApiKeyStatus();
  }, []);

  const fetchStats = async () => {
    try {
      const r = await axios.get(`${API_URL}/stats`);
      setStats(r.data);
    } catch {
      /* silent */
    }
  };

  const fetchApiKeyStatus = async () => {
    try {
      const r = await axios.get(`${API_URL}/api-key`);
      setApiKeyStatus(r.data);
    } catch {
      /* silent */
    }
  };

  const handleSaveApiKey = async () => {
    setApiKeyError('');
    setApiKeySuccess('');
    if (!apiKeyInput.trim()) {
      setApiKeyError('Enter an API key');
      return;
    }
    setApiKeySaving(true);
    try {
      await axios.post(`${API_URL}/api-key`, { key: apiKeyInput.trim(), provider: apiKeyProvider });
      setApiKeySuccess('API key saved. System reloaded.');
      setApiKeyInput('');
      fetchApiKeyStatus();
      setTimeout(() => { setApiKeySuccess(''); setShowApiKeyModal(false); }, 2000);
    } catch (e: any) {
      setApiKeyError(e.response?.data?.detail || 'Failed to save API key');
    } finally {
      setApiKeySaving(false);
    }
  };

  const handleSend = async (text?: string) => {
    const value = (text ?? input).trim();
    if (!value || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: value }]);
    setInput('');
    setLoading(true);

    try {
      const r = await axios.post(`${API_URL}/chat`, { message: value });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: r.data.text,
          artifacts: r.data.artifacts,
          images: r.data.images,
          technicalResponse: r.data.technical_response,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Backend error. Check that the API is running and try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try { await axios.post(`${API_URL}/reset`); } catch { /* silent */ }
    setMessages([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div className="flex h-screen flex-col bg-[#f3f0ea] text-slate-900">
      {/* ── Top bar ─────────────────────────────────────────────── */}
      <header className="flex shrink-0 items-center justify-between border-b border-slate-200/70 bg-white/80 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white shadow-lg shadow-slate-950/15">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-black leading-tight tracking-tight text-slate-950 sm:text-xl">
              Vulcan OmniPro 220
            </h1>
            <p className="hidden text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 sm:block">
              Executable Knowledge Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {stats && (
            <span className="hidden text-[11px] font-semibold text-slate-500 sm:block">
              {stats.knowledge_nodes ?? stats.text_chunks ?? 0} nodes · {stats.relationships ?? 0} links
            </span>
          )}
          {apiKeyStatus && (
            <span className="flex items-center gap-1 rounded-lg bg-slate-50 px-2 py-1 text-[11px] font-semibold text-slate-500 ring-1 ring-slate-200/80">
              <Key className="h-3 w-3" />
              {apiKeyStatus.configured ? apiKeyStatus.provider : 'No LLM key'}
            </span>
          )}
          <button
            onClick={() => { setShowApiKeyModal(true); setApiKeyError(''); setApiKeySuccess(''); }}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            title="API Key Settings"
          >
            <Settings className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Settings</span>
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            title="Reset"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </header>

      {/* ── Chat area ───────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-5">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'user' ? (
                <div className="max-w-lg rounded-2xl bg-slate-950 px-4 py-3 text-sm text-white shadow-lg">
                  {msg.content}
                </div>
              ) : (
                <AssistantSurface message={msg} />
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2.5 rounded-2xl bg-white px-4 py-3 shadow ring-1 ring-slate-200/80">
                <Loader2 className="h-4 w-4 animate-spin text-teal-600" />
                <span className="text-sm font-medium text-slate-600">Simulating state…</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* ── Quick queries — only on empty state ─────────────────── */}
      {messages.length === 0 && !loading && (
        <div className="mx-auto max-w-4xl px-4 pb-2 sm:px-6">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {quickQueries.map((q) => (
              <button
                key={q.label}
                onClick={() => handleSend(q.prompt)}
                className="group flex items-center justify-between rounded-xl border border-slate-200/80 bg-white px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-md"
              >
                <span className="text-[13px] font-medium leading-snug text-slate-800">{q.prompt}</span>
                <OutcomeMiniBadge badge={q.badge} />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Input bar ───────────────────────────────────────────── */}
      <div className="border-t border-slate-200/70 bg-white/80 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="mx-auto max-w-4xl flex gap-2.5">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about setup, polarity, duty cycle, or a defect…"
            className="min-h-[44px] flex-1 resize-none rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="flex shrink-0 items-center gap-2 rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-950/15 transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            <span className="hidden sm:inline">Run</span>
          </button>
        </div>
      </div>

      {/* ── API Key Modal ─────────────────────────────────────── */}
      {showApiKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={() => setShowApiKeyModal(false)}>
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-black/5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900">API Key Settings</h3>
              <button onClick={() => setShowApiKeyModal(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600">
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="mt-1 text-xs text-slate-500">Add your own API key to enable LLM-powered query parsing and explanations. The system works without one (fallback mode).</p>

            <div className="mt-4">
              <label className="mb-1 block text-xs font-semibold text-slate-700">Provider</label>
              <div className="flex gap-2">
                {(['openrouter', 'anthropic'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setApiKeyProvider(p)}
                    className={`flex-1 rounded-lg px-3 py-2 text-xs font-semibold transition ring-1 ${
                      apiKeyProvider === p
                        ? 'bg-slate-950 text-white ring-slate-950'
                        : 'bg-white text-slate-700 ring-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    {p === 'openrouter' ? 'OpenRouter' : 'Anthropic'}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-3">
              <label className="mb-1 block text-xs font-semibold text-slate-700">API Key</label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSaveApiKey(); }}
                placeholder={apiKeyProvider === 'openrouter' ? 'sk-or-v1-...' : 'sk-ant-...'}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
              />
            </div>

            <p className="mt-2 text-[11px] text-slate-400">
              {apiKeyProvider === 'openrouter'
                ? 'OpenRouter key from openrouter.ai/keys'
                : 'Anthropic key from console.anthropic.com'}
            </p>

            {apiKeyError && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700 ring-1 ring-rose-200">
                <TriangleAlert className="h-3.5 w-3.5" />
                {apiKeyError}
              </div>
            )}
            {apiKeySuccess && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700 ring-1 ring-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {apiKeySuccess}
              </div>
            )}

            <button
              onClick={handleSaveApiKey}
              disabled={apiKeySaving}
              className="mt-4 w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-slate-900 disabled:opacity-50"
            >
              {apiKeySaving ? 'Saving…' : 'Save & Reload'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  OutcomeMiniBadge — tiny badge for quick-query buttons               */
/* ------------------------------------------------------------------ */

function OutcomeMiniBadge({ badge }: { badge: string }) {
  const c: Record<string, string> = {
    SAFE: 'bg-emerald-100 text-emerald-700',
    'SUBOPTIMAL': 'bg-amber-100 text-amber-700',
    'FAILURE RISK': 'bg-rose-100 text-rose-700',
    'DAMAGE RISK': 'bg-slate-900 text-white',
    'INSUFFICIENT_STATE': 'bg-gray-200 text-gray-600',
  };
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold ${c[badge] ?? 'bg-gray-200 text-gray-600'}`}>
      {badge}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  AssistantSurface — renders a single assistant reply                  */
/* ------------------------------------------------------------------ */

function AssistantSurface({ message }: { message: Message }) {
  const explanation = message.technicalResponse?.explanation || message.content;
  const stateItems = buildMachineStateItems(message);
  const outcome = deriveOutcome(message);
  const confidenceMeta = getConfidenceMeta(message.technicalResponse?.confidence, outcome.level);
  const decision = message.technicalResponse?.instruction || outcome.assertion;
  const consequences = message.technicalResponse?.consequences ?? [];
  const hasTechnicalDetails =
    Boolean(message.technicalResponse?.assumptions?.length) ||
    Boolean(message.technicalResponse?.sources?.length) ||
    Boolean(message.technicalResponse?.simulation?.length) ||
    Boolean(message.technicalResponse?.constraint_trace?.length) ||
    Boolean(message.images?.length);

  return (
    <div className="w-full overflow-hidden rounded-2xl bg-white/90 shadow-lg ring-1 ring-black/5 backdrop-blur">
      {/* Artifact — primary answer */}
      {message.artifacts && message.artifacts.length > 0 && (
        <div className="px-3 pt-3 sm:px-4 sm:pt-4">
          {message.artifacts.map((a, i) => (
            <ArtifactRenderer key={i} type={a.type} title={a.title} data={a.data} />
          ))}
        </div>
      )}

      <div className="space-y-3 px-3 pb-4 pt-2 sm:px-4 sm:pb-5">
        {/* Outcome */}
        <section className={`rounded-xl px-4 py-3 ring-1 ${outcome.panelClass}`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-black ${outcome.badgeClass}`}>
                {outcome.icon}
                {outcome.headline}
              </span>
              <span className="text-xs font-semibold text-slate-700">{outcome.assertion}</span>
            </div>
            {confidenceMeta && (
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${confidenceMeta.className}`}>
                {confidenceMeta.icon}
                {confidenceMeta.label}
              </span>
            )}
          </div>
          {message.technicalResponse?.outcome?.reason && (
            <p className="mt-1.5 text-[11px] text-slate-500">{message.technicalResponse.outcome.reason}</p>
          )}
        </section>

        {/* Machine state */}
        {stateItems.length > 0 && (
          <section className="rounded-xl bg-slate-950 px-4 py-3 text-white">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Machine state</p>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              {stateItems.map((item) => (
                <div key={item.label} className="rounded-lg bg-white/8 px-3 py-2 ring-1 ring-white/10">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">{item.label}</p>
                  <p className="mt-0.5 text-sm font-semibold text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Decision + explanation */}
        <section className="rounded-xl bg-slate-50/80 px-4 py-3 ring-1 ring-slate-200/80">
          <p className="m-0 text-sm font-semibold leading-relaxed text-slate-900">{decision}</p>
          <p className="m-0 mt-1 text-sm leading-relaxed text-slate-600">{explanation}</p>
        </section>

        {/* Consequences */}
        {consequences.length > 0 && (
          <section className="rounded-xl bg-slate-50/80 px-4 py-3 ring-1 ring-slate-200/80">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <TriangleAlert className="h-3.5 w-3.5 text-rose-500" />
              Consequence chain
            </p>
            <div className="grid gap-2 md:grid-cols-3">
              {consequences.map((c) => (
                <div key={c.label} className="rounded-lg bg-white px-3 py-2.5 ring-1 ring-slate-200/80">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{c.label}</p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-700">{c.text}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Collapsible technical details */}
        {hasTechnicalDetails && (
          <details className="group rounded-xl bg-slate-50/70 ring-1 ring-slate-200/80">
            <summary className="flex cursor-pointer items-center justify-between px-4 py-2.5 text-xs font-semibold text-slate-600 list-none">
              Technical details
              <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" />
            </summary>
            <div className="border-t border-slate-200/80 px-4 py-3 grid gap-3 md:grid-cols-2">
              {message.technicalResponse?.assumptions?.length ? (
                <DetailList title="Assumptions">
                  {message.technicalResponse.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                </DetailList>
              ) : null}
              {message.technicalResponse?.sources?.length ? (
                <DetailList title="Sources">
                  {message.technicalResponse.sources.map((s, i) => (
                    <li key={i}>{s.source} p.{s.page} · {s.node_type}</li>
                  ))}
                </DetailList>
              ) : null}
              {message.technicalResponse?.constraint_trace?.length ? (
                <DetailList title="Constraints">
                  {message.technicalResponse.constraint_trace.map((c, i) => (
                    <li key={i}>
                      <span className={c.passed ? 'text-emerald-600' : 'text-rose-600'}>
                        {c.passed ? 'PASS' : 'FAIL'}
                      </span>{' '}
                      {c.rule}: {c.detail}
                    </li>
                  ))}
                </DetailList>
              ) : null}
            </div>
          </details>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function DetailList({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">{title}</p>
      <ul className="mt-1.5 space-y-1 text-xs leading-relaxed text-slate-600">{children}</ul>
    </div>
  );
}

function buildMachineStateItems(message: Message) {
  const state = message.technicalResponse?.state || {};
  const artifactData = message.artifacts?.[0]?.data || {};
  const items: { label: string; value: string }[] = [];

  const push = (label: string, value?: string | number | null) => {
    if (!value || items.some((i) => i.label === label)) return;
    items.push({ label, value: String(value) });
  };

  push('Process', state.process || artifactData.process);
  push('Material', state.material || artifactData.defaultMaterial);
  push('Thickness', state.thickness || artifactData.defaultThickness);
  push('Voltage', state.components?.powerSource?.inputVoltage || state.inputVoltage);
  push(
    'Amperage',
    artifactData.recommendedStartAmperage
      ? `${artifactData.recommendedStartAmperage}A`
      : state.constraints?.targetAmperage
        ? `${state.constraints.targetAmperage}A`
        : state.targetAmperage
          ? `${state.targetAmperage}A`
          : artifactData.amperage
            ? `${artifactData.amperage}A`
            : undefined
  );
  push('Polarity', state.constraints?.expectedPolarity || artifactData.polarity);
  push('Duty cycle', artifactData.dutyCycle ? `${artifactData.dutyCycle}%` : undefined);
  push('Current flow', state.derived?.currentFlow === 'balanced' ? 'Balanced' : state.derived?.currentFlow);
  push('Outcome', summarizeOutcome(state.derived?.weldOutcome));

  return items.slice(0, 4);
}

function getConfidenceMeta(confidence: { label: string; score: number } | undefined, level: OutcomeLevel) {
  if (!confidence) return null;
  if (level === 'SAFE') return { label: 'Reliable', className: 'bg-emerald-100 text-emerald-700', icon: <ShieldCheck className="h-3 w-3" /> };
  if (level === 'DAMAGE RISK') return { label: 'Stop', className: 'bg-rose-100 text-rose-700', icon: <TriangleAlert className="h-3 w-3" /> };
  if (confidence.score >= 0.78) return { label: 'Reliable', className: 'bg-emerald-100 text-emerald-700', icon: <ShieldCheck className="h-3 w-3" /> };
  if (confidence.score >= 0.55) return { label: 'Approximate', className: 'bg-amber-100 text-amber-700', icon: <Gauge className="h-3 w-3" /> };
  return { label: 'Review', className: 'bg-rose-100 text-rose-700', icon: <TriangleAlert className="h-3 w-3" /> };
}

function deriveOutcome(message: Message): { level: OutcomeLevel; headline: string; icon: React.ReactNode; badgeClass: string; panelClass: string; assertion: string } {
  const level = message.technicalResponse?.outcome?.level ?? 'FAILURE RISK';
  const headline = message.technicalResponse?.outcome?.headline ?? 'UNKNOWN';
  const meta: Record<string, { icon: React.ReactNode; badgeClass: string; panelClass: string; assertion: string }> = {
    SAFE: {
      icon: <ShieldCheck className="h-3.5 w-3.5" />,
      badgeClass: 'bg-emerald-600 text-white',
      panelClass: 'bg-emerald-50/90 ring-emerald-200/80',
      assertion: 'Setup is valid.',
    },
    SUBOPTIMAL: {
      icon: <Gauge className="h-3.5 w-3.5" />,
      badgeClass: 'bg-amber-500 text-white',
      panelClass: 'bg-amber-50/90 ring-amber-200/80',
      assertion: 'Valid, but wastes thermal margin.',
    },
    'FAILURE RISK': {
      icon: <TriangleAlert className="h-3.5 w-3.5" />,
      badgeClass: 'bg-rose-600 text-white',
      panelClass: 'bg-rose-50/90 ring-rose-200/80',
      assertion: 'Invalid state. Weld will fail.',
    },
    'DAMAGE RISK': {
      icon: <TriangleAlert className="h-3.5 w-3.5" />,
      badgeClass: 'bg-slate-950 text-white',
      panelClass: 'bg-[linear-gradient(135deg,rgba(127,29,29,0.08),rgba(15,23,42,0.08))] ring-rose-300/80',
      assertion: 'Correct before welding. Equipment damage likely.',
    },
    'INSUFFICIENT_STATE': {
      icon: <TriangleAlert className="h-3.5 w-3.5" />,
      badgeClass: 'bg-gray-400 text-white',
      panelClass: 'bg-gray-50/90 ring-gray-200/80',
      assertion: 'More information required.',
    },
  };
  const m = meta[level] ?? meta['FAILURE RISK'];
  return { level, headline, ...m };
}

function summarizeOutcome(v?: string) {
  if (!v) return undefined;
  if (v.includes('stable arc')) return 'Stable arc';
  if (v.includes('poor penetration')) return 'Weak penetration';
  return v.charAt(0).toUpperCase() + v.slice(1);
}

export default App;
