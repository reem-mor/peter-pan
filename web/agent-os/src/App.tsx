import { NavLink, Navigate, Route, Routes } from "react-router-dom";

const SECTIONS = [
  { path: "/incidents", label: "Incidents" },
  { path: "/deployments", label: "Deployments" },
  { path: "/on-call", label: "On-call" },
  { path: "/token-usage", label: "Token Usage" },
  { path: "/system-map", label: "System Map" },
  { path: "/post-mortems", label: "Post-mortems" },
] as const;

function SectionPage({ title }: { title: string }) {
  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 text-sm text-ink-soft">
        Placeholder — this surface is built in a later workstream.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div className="flex h-screen bg-surface font-display text-ink">
      <aside className="flex w-56 shrink-0 flex-col bg-sidebar text-sidebar-ink">
        <div className="px-5 py-5">
          <p className="text-xs font-semibold tracking-widest text-white uppercase">
            PETER PAN OS
          </p>
          <p className="mt-1 text-[11px] opacity-70">operator console</p>
        </div>
        <nav className="flex flex-col gap-1 px-3">
          {SECTIONS.map((section) => (
            <NavLink
              key={section.path}
              to={section.path}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-white/10 font-medium text-white"
                    : "hover:bg-white/5 hover:text-white"
                }`
              }
            >
              {section.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-5 py-4 text-[11px] opacity-60">
          synthetic data only
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Navigate to="/incidents" replace />} />
          {SECTIONS.map((section) => (
            <Route
              key={section.path}
              path={section.path}
              element={<SectionPage title={section.label} />}
            />
          ))}
          <Route path="*" element={<SectionPage title="Not found" />} />
        </Routes>
      </main>
    </div>
  );
}
