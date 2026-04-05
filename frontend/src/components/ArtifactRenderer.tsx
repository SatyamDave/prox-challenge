/**
 * Renders representation-aware artifacts returned by the backend.
 */

import React from 'react';
import { ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';

type ArtifactType =
  | 'polarity_diagram'
  | 'duty_cycle_visualizer'
  | 'troubleshooting_tree'
  | 'parameter_explorer'
  | 'interactive_table';

interface ArtifactProps {
  type: ArtifactType;
  title: string;
  data: any;
}

const ArtifactRenderer: React.FC<ArtifactProps> = ({ type, title, data }) => {
  const badgeToneClass = (tone: string) => {
    if (tone === 'danger') return 'border-rose-200/80 bg-rose-50 text-rose-800';
    if (tone === 'warning') return 'border-amber-200/80 bg-amber-50 text-amber-800';
    if (tone === 'success') return 'border-emerald-200/80 bg-emerald-50 text-emerald-800';
    return 'border-cyan-200/80 bg-cyan-50 text-cyan-800';
  };

  const outcomeTone = (outcome?: string) => {
    if (outcome === 'DAMAGE RISK' || outcome === 'FAILURE RISK') return 'danger';
    if (outcome === 'SUBOPTIMAL') return 'warning';
    if (outcome === 'SAFE') return 'success';
    return 'info';
  };

  const renderHeatBar = (label: string, torchHeat: number, workpieceHeat: number, tone: 'emerald' | 'rose') => (
    <div className="rounded-[1.5rem] bg-white/88 p-4 shadow-sm ring-1 ring-slate-200/70 backdrop-blur">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</div>
      <div className="mt-4 space-y-3">
        <MetricBar
          label="Torch heat"
          value={Math.round(torchHeat * 100)}
          colorClass={tone === 'rose' ? 'bg-rose-500' : 'bg-emerald-500'}
        />
        <MetricBar
          label="Workpiece heat"
          value={Math.round(workpieceHeat * 100)}
          colorClass={tone === 'rose' ? 'bg-amber-500' : 'bg-cyan-500'}
        />
      </div>
    </div>
  );

  const renderPolarityDiagram = () => {
    // Determine the tone based on the backend's outcome
    const currentTone = outcomeTone(data.outcome);
    const isFailure = currentTone === 'danger';

    const renderStateDiagram = (
      state: any,
      tone: 'success' | 'danger',
      titleLabel: string,
      subtitle: string,
      diagramId: string // Added diagramId for unique marker IDs
    ) => {
      const torchTerminal = state?.components?.torch?.terminal || 'negative';
      const workTerminal = state?.components?.workClamp?.terminal || 'positive';
      const heat = state?.derived?.heatDistribution || { torch: 0.3, workpiece: 0.7 };

      return (
        <div className={`rounded-[1.5rem] p-4 ring-1 ${tone === 'danger' ? 'bg-rose-50/90 ring-rose-200/80' : 'bg-emerald-50/90 ring-emerald-200/80'}`}>
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{titleLabel}</div>
              <div className="mt-1 text-lg font-black text-slate-950">{subtitle}</div>
            </div>
            <div className={`rounded-full px-3 py-1 text-sm font-semibold ${tone === 'danger' ? 'bg-rose-500 text-white' : 'bg-emerald-600 text-white'}`}>
              {torchTerminal === 'negative' ? 'DCEN' : 'DCEP'}
            </div>
          </div>

          <svg width="100%" height="250" viewBox="0 0 560 250" className="overflow-visible">
            <defs>
              <marker id={`flow-arrow-${diagramId}-${titleLabel}`} markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill={tone === 'danger' ? '#e11d48' : '#0f766e'} />
              </marker>
            </defs>

            <rect x="22" y="82" width="130" height="88" rx="18" fill="#0f172a" />
            <text x="87" y="128" textAnchor="middle" fill="white" fontSize="15" fontWeight="700">Welder</text>

            <circle cx="164" cy="103" r="15" fill="#dc2626" />
            <text x="164" y="107" textAnchor="middle" fill="white" fontSize="13" fontWeight="700">+</text>
            <circle cx="164" cy="147" r="15" fill="#111827" />
            <text x="164" y="151" textAnchor="middle" fill="white" fontSize="13" fontWeight="700">-</text>

            <rect x="392" y="46" width="122" height="50" rx="16" fill="#2563eb" />
            <text x="453" y="76" textAnchor="middle" fill="white" fontSize="14" fontWeight="700">Torch</text>

            <rect x="386" y="170" width="132" height="54" rx="16" fill="#6b7280" />
            <text x="452" y="202" textAnchor="middle" fill="white" fontSize="14" fontWeight="700">Workpiece</text>

            <line
              x1="164"
              y1={torchTerminal === 'negative' ? 147 : 103}
              x2="392"
              y2="71"
              stroke={tone === 'danger' ? '#e11d48' : '#0f766e'}
              strokeWidth="6"
              strokeLinecap="round"
              markerEnd={`url(#flow-arrow-${diagramId}-${titleLabel})`}
            />
            <line
              x1="164"
              y1={workTerminal === 'positive' ? 103 : 147}
              x2="386"
              y2="197"
              stroke={tone === 'danger' ? '#fb7185' : '#06b6d4'}
              strokeWidth="6"
              strokeLinecap="round"
              markerEnd={`url(#flow-arrow-${diagramId}-${titleLabel})`}
            />

            <text x="275" y="52" textAnchor="middle" fill="#475569" fontSize="12" fontWeight="700">
              Torch on {torchTerminal}
            </text>
            <text x="274" y="226" textAnchor="middle" fill="#475569" fontSize="12" fontWeight="700">
              Work clamp on {workTerminal}
            </text>
          </svg>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {renderHeatBar('Heat distribution', heat.torch, heat.workpiece, tone === 'danger' ? 'rose' : 'emerald')}
            <div className={`rounded-[1.5rem] p-4 ring-1 ${tone === 'danger' ? 'bg-white ring-rose-200/80' : 'bg-white ring-emerald-200/80'}`}>
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Outcome</div>
              <div className="mt-3 text-sm font-medium leading-6 text-slate-700">
                {state?.derived?.weldOutcome || 'Stable arc'}
              </div>
            </div>
          </div>
        </div>
      );
    };

    return (
      <div className="space-y-5 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,_rgba(15,118,110,0.14),_transparent_32%),linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.98))] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Visual answer</div>
            <div className="mt-2 flex items-center gap-2 text-2xl font-black text-slate-950">
              {isFailure ? <ShieldAlert className="h-6 w-6 text-rose-500" /> : <CheckCircle2 className="h-6 w-6 text-emerald-500" />}
              <span>{isFailure ? 'Computed Failure State' : 'Computed Safe State'}</span>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              The diagram below shows the computed machine state and its transition.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.statusBadges?.map((badge: any, index: number) => (
              <span key={index} className={`rounded-full border px-3 py-1 text-xs font-semibold ${badgeToneClass(badge.tone)}`}>
                {badge.label}
              </span>
            ))}
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1fr_auto_1fr] xl:items-center">
          {data.comparison?.before && renderStateDiagram(data.comparison.before, 'success', 'Initial State', 'Expected baseline configuration', 'before')}
          <div className="hidden xl:flex h-full items-center justify-center">
            <div className={`flex h-12 w-12 items-center justify-center rounded-full ${isFailure ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-600'}`}>
              <ArrowRight className="h-5 w-5" />
            </div>
          </div>
          {data.comparison?.after && renderStateDiagram(data.comparison.after, isFailure ? 'danger' : 'success', 'Computed State', isFailure ? 'Resulting failure configuration' : 'Resulting safe configuration', 'after')}
        </div>

        <div className={`rounded-[1.5rem] px-5 py-4 text-sm font-medium shadow-sm ring-1 ${isFailure ? 'bg-rose-50 text-rose-900 ring-rose-200/80' : 'bg-emerald-50 text-emerald-900 ring-emerald-200/80'}`}>
          {isFailure
            ? 'The computed state indicates a critical issue. Reverse polarity drives heat into the tungsten immediately. The torch overheats, contamination starts, and the weld fails.'
            : 'The computed state is safe. Correct polarity keeps heat in the workpiece. The arc stays stable, penetration holds, and the tungsten stays protected.'}
        </div>
      </div>
    );
  };

  const renderDutyCycleVisualizer = () => {
    const amperage = data.amperage;
    const voltage = data.voltage;
    const process = data.process;

    const lookupKey = `${process}_${amperage}A_${voltage}V`;
    const dutyCycle = data.calculator?.lookupTable?.[lookupKey] ?? data.dutyCycle ?? 40;
    const weldTime = ((dutyCycle / 100) * data.timeWindow).toFixed(1);
    const coolTime = (data.timeWindow - Number(weldTime)).toFixed(1);
    const riskTone = outcomeTone(data.outcome);

    return (
      <div className="space-y-5 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,_rgba(6,182,212,0.14),_transparent_30%),linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.98))] p-5">
        <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-[1.5rem] bg-white/92 p-5 shadow-sm ring-1 ring-slate-200/70">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Thermal window</div>
                <div className="mt-2 text-5xl font-black text-slate-950">{dutyCycle}%</div>
                <div className="mt-2 text-sm text-slate-500">{process} at {voltage}V</div>
              </div>
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${badgeToneClass(riskTone)}`}>
                {data.outcomeHeadline}
              </span>
            </div>

            <div className="mt-6 overflow-hidden rounded-full bg-slate-100">
              <div className="flex h-6">
                <div className="bg-rose-500 transition-all" style={{ width: `${dutyCycle}%` }} />
                <div className="bg-cyan-400 transition-all" style={{ width: `${100 - dutyCycle}%` }} />
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <MetricTile label="Weld window" value={`${weldTime} min`} tone={riskTone} />
              <MetricTile label="Cooldown" value={`${coolTime} min`} tone="info" />
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTroubleshootingTree = () => {
    const [activeNode, setActiveNode] = React.useState(data.rootNode);
    const node = data.nodes?.find((entry: any) => entry.id === activeNode);

    if (!node) {
      return <div className="rounded-[1.75rem] bg-white p-5 text-slate-500">No troubleshooting data available.</div>;
    }

    return (
      <div className="space-y-5 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.13),_transparent_28%),linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.98))] p-5">
        <div className="rounded-[1.5rem] bg-slate-950 px-5 py-5 text-white">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-emerald-300">Diagnosis path</div>
          <div className="mt-2 text-2xl font-black">{data.problem}</div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
            Work the flow left to right and fix the fastest reversible cause first.
          </p>
        </div>

        <div className="rounded-[1.5rem] bg-white/92 p-5 shadow-sm ring-1 ring-slate-200/70">
          <div className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">Current prompt</div>
          <div className="mt-2 text-xl font-black text-slate-950">{node.text}</div>

          {node.options?.length > 0 && (
            <div className="mt-5 grid gap-3">
              {node.options.map((option: any) => (
                <button
                  key={option.label}
                  onClick={() => setActiveNode(option.next)}
                  className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-left text-sm font-medium text-slate-700 transition hover:-translate-y-0.5 hover:border-emerald-300 hover:bg-emerald-50"
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}

          {node.steps?.length > 0 && (
            <div className="mt-5 grid gap-3">
              {node.steps.map((step: string, index: number) => (
                <div key={index} className="rounded-[1.25rem] bg-slate-50 px-4 py-4 ring-1 ring-slate-200/70">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Step {index + 1}</div>
                  <div className="mt-2 text-sm leading-6 text-slate-700">{step}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderParameterExplorer = () => (
    <div className="space-y-5 rounded-[1.75rem] bg-[radial-gradient(circle_at_top,_rgba(139,92,246,0.14),_transparent_28%),linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.98))] p-5">
      <div className="rounded-[1.5rem] bg-slate-950 px-5 py-5 text-white">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-violet-300">Recommended setup</div>
        <div className="mt-2 grid gap-3 md:grid-cols-3">
          <StateValue label="Process" value={data.process} />
          <StateValue label="Material" value={data.defaultMaterial} />
          <StateValue label="Thickness" value={data.defaultThickness} />
        </div>
      </div>

      {data.parameterCards?.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {data.parameterCards.map((card: any, index: number) => (
            <div key={index} className={`rounded-[1.5rem] px-4 py-5 shadow-sm ring-1 ${badgeToneClass(card.tone)}`}>
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] opacity-70">{card.label}</div>
              <div className="mt-3 text-3xl font-black leading-none">{card.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="rounded-[1.5rem] bg-white/92 p-5 shadow-sm ring-1 ring-slate-200/70">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Load envelope</div>
          <div className="mt-2 text-2xl font-black text-slate-950">
            {data.amperageRange?.[0]}A - {data.amperageRange?.[1]}A
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Start near {data.recommendedStartAmperage}A, then tune from bead profile and puddle control.
          </p>
        </div>

        <div className="rounded-[1.5rem] bg-white/92 p-5 shadow-sm ring-1 ring-slate-200/70">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Adjustment notes</div>
          <div className="mt-3 grid gap-3">
            {data.notes?.map((note: string, index: number) => (
              <div key={index} className="rounded-[1.25rem] bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700 ring-1 ring-slate-200/70">
                {note}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderInteractiveTable = () => (
    <div className="overflow-hidden rounded-[1.75rem] bg-white/95 shadow-sm ring-1 ring-slate-200/80">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-950">
          <tr>
            {data.headers?.map((header: string, index: number) => (
              <th
                key={index}
                className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-300"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.rows?.map((row: string[], rowIndex: number) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-4 text-sm text-slate-700">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="my-4 overflow-hidden rounded-[2rem] bg-white/55 shadow-[0_26px_80px_-45px_rgba(15,23,42,0.75)] ring-1 ring-white/55 backdrop-blur">
      <div className="border-b border-slate-200/80 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Primary artifact</div>
            <h3 className="app-display mt-1 text-2xl font-black text-white">{title}</h3>
          </div>
          {data.statusBadges?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {data.statusBadges.map((badge: any, index: number) => (
                <span key={index} className={`rounded-full border px-3 py-1 text-xs font-semibold ${badgeToneClass(badge.tone)}`}>
                  {badge.label}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-4 sm:p-5">
        {type === 'polarity_diagram' && renderPolarityDiagram()}
        {type === 'duty_cycle_visualizer' && renderDutyCycleVisualizer()}
        {type === 'troubleshooting_tree' && renderTroubleshootingTree()}
        {type === 'parameter_explorer' && renderParameterExplorer()}
        {type === 'interactive_table' && renderInteractiveTable()}
      </div>
    </div>
  );
};

function MetricBar({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: number;
  colorClass: string;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${colorClass}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function MetricTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: 'danger' | 'warning' | 'success' | 'info';
}) {
  const toneClass =
    tone === 'danger'
      ? 'bg-rose-50 text-rose-900 ring-rose-200/70'
      : tone === 'warning'
        ? 'bg-amber-50 text-amber-900 ring-amber-200/70'
        : tone === 'success'
          ? 'bg-emerald-50 text-emerald-900 ring-emerald-200/70'
          : 'bg-cyan-50 text-cyan-900 ring-cyan-200/70';

  return (
    <div className={`rounded-[1.25rem] px-4 py-4 ring-1 ${toneClass}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] opacity-70">{label}</div>
      <div className="mt-2 text-xl font-black">{value}</div>
    </div>
  );
}

function StateValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.25rem] bg-white/8 px-4 py-4 ring-1 ring-white/10">
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">{label}</div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

export default ArtifactRenderer;
