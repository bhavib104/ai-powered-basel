import { NavLink, Outlet } from "react-router-dom";

import { HealthBadge } from "./HealthBadge";

interface NavItem {
  to: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard" },
  { to: "/exposures", label: "Exposures" },
  { to: "/risk", label: "Risk & RWA" },
  { to: "/data-quality", label: "Data Quality" },
  { to: "/reconciliation", label: "Reconciliation" },
  { to: "/documents", label: "Regulatory Documents" },
  { to: "/assistant", label: "AI Risk Assistant" },
  { to: "/audit", label: "Audit & Runs" },
];

export function AppLayout() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-sm font-bold text-white">
              BR
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Basel Risk Intelligence
              </p>
              <p className="text-xs text-slate-500">
                Deterministic risk · AI-assisted document intelligence
              </p>
            </div>
          </div>
          <HealthBadge />
        </div>
        <nav className="mx-auto flex max-w-7xl flex-wrap gap-1 px-4 pb-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-4">
        <p className="mx-auto max-w-7xl px-6 text-xs text-slate-400">
          Educational project · 100% synthetic data · Not for regulatory submission
        </p>
      </footer>
    </div>
  );
}
