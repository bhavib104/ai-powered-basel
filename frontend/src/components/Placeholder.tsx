import type { ReactNode } from "react";

interface PlaceholderProps {
  title: string;
  phase: string;
  description: string;
  children?: ReactNode;
}

/**
 * Honest placeholder for a page whose feature has not been built yet.
 *
 * It states exactly what will appear here and in which phase — it never shows
 * fake numbers or non-functional buttons.
 */
export function Placeholder({ title, phase, description, children }: PlaceholderProps) {
  return (
    <section className="space-y-4">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
          Planned · {phase}
        </span>
      </header>
      <p className="max-w-3xl text-sm leading-relaxed text-slate-600">{description}</p>
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        <p>
          This page is intentionally empty until its backend feature exists. It will
          display real data from the API — no hardcoded or sample metrics.
        </p>
        {children}
      </div>
    </section>
  );
}
