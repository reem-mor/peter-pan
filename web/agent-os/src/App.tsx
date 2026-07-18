import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { HealthStrip } from "./components/HealthStrip";
import { TokenUsage } from "./pages/TokenUsage";
import { Incidents } from "./pages/Incidents";
import { Deployments } from "./pages/Deployments";
import { OnCall } from "./pages/OnCall";
import { PostMortems } from "./pages/PostMortems";
import { SystemMap } from "./pages/SystemMap";

const SECTIONS = [
  { path: "/token-usage", label: "Token Usage", element: <TokenUsage /> },
  { path: "/incidents", label: "Incidents", element: <Incidents /> },
  { path: "/deployments", label: "Deployments", element: <Deployments /> },
  { path: "/on-call", label: "On-call", element: <OnCall /> },
  { path: "/post-mortems", label: "Post-mortems", element: <PostMortems /> },
  { path: "/system-map", label: "System Map", element: <SystemMap /> },
] as const;

function NotFound() {
  return (
    <div className="p-8">
      <h1 className="font-mono text-lg font-bold text-ink">Not found</h1>
      <p className="mt-2 text-sm text-ink-soft">
        No such surface. Pick a section from the sidebar.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div className="flex h-screen bg-bg font-display text-ink">
      <a
        href="#main"
        className="absolute -left-full top-0 z-50 rounded-br-lg bg-accent px-4 py-2.5 font-mono font-bold text-bg focus:left-0"
      >
        Skip to content
      </a>

      <aside className="flex w-56 shrink-0 flex-col border-r border-edge bg-panel">
        <div className="px-5 py-5">
          <div className="flex items-center gap-2.5">
            <span
              aria-hidden="true"
              className="grid h-8 w-8 place-items-center rounded-lg border border-accent bg-accent-dim font-mono text-sm font-bold text-accent"
            >
              ✦
            </span>
            <div>
              <p className="font-mono text-xs font-bold tracking-[0.14em] text-ink uppercase">
                Peter Pan OS
              </p>
              <p className="font-mono text-[10px] tracking-[0.18em] text-ink-faint uppercase">
                operator console
              </p>
            </div>
          </div>
        </div>
        <nav className="flex flex-col gap-1 px-3" aria-label="Console sections">
          {SECTIONS.map((section) => (
            <NavLink
              key={section.path}
              to={section.path}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 font-mono text-[13px] transition-colors ${
                  isActive
                    ? "border border-accent/40 bg-accent-dim font-semibold text-accent"
                    : "border border-transparent text-ink-soft hover:bg-panel-2 hover:text-ink"
                }`
              }
            >
              {section.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-5 py-4 font-mono text-[10.5px] tracking-[0.1em] text-ink-faint uppercase">
          synthetic data only
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <HealthStrip />
        <main id="main" className="min-w-0 flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/token-usage" replace />} />
            {SECTIONS.map((section) => (
              <Route
                key={section.path}
                path={section.path}
                element={section.element}
              />
            ))}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
