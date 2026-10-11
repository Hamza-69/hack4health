import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router";
import { api, type Module } from "./api";
import { useAuth } from "./auth";

export type LayoutContext = { modules: Module[] };

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `block rounded-md px-3 py-2 text-sm ${isActive ? "bg-[#0d5c48] text-white" : "text-gray-700 hover:bg-gray-200"}`;

export default function Layout() {
  const { admin, logout } = useAuth();
  const [modules, setModules] = useState<Module[]>([]);

  useEffect(() => {
    api<Module[]>("/admin/modules").then(setModules).catch(console.error);
  }, []);

  return (
    <div className="flex h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-gray-200 bg-gray-100 p-4">
        <div className="mb-6 flex items-center gap-3 px-3">
          <img src="/favicon.svg" alt="" className="h-9 w-9 rounded-[10px]" />
          <div>
            <div className="font-semibold">Wasel · واصل</div>
            <div className="text-xs text-gray-500">وزارة الصحة العامة · Ministry of Public Health</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          <NavLink to="/tickets" className={linkClass}>
            Tickets
          </NavLink>
          {modules.length > 0 && (
            <div className="px-3 pt-4 pb-1 text-xs font-medium tracking-wide text-gray-500 uppercase">Modules</div>
          )}
          {modules.map((m) => (
            <NavLink key={m.name} to={`/m/${m.name}`} className={linkClass}>
              {m.title}
            </NavLink>
          ))}
        </nav>
        <p className="mb-3 px-3 text-xs leading-snug text-gray-500">
          Staff see requests and anonymous questions, never patients' chats.
        </p>
        <div className="border-t border-gray-200 px-3 pt-4 text-sm">
          <div className="truncate">{admin?.email}</div>
          <div className="text-gray-500">{admin?.role}</div>
          <button onClick={logout} className="mt-2 text-gray-600 underline hover:text-gray-900">
            Log out
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto">
        <Outlet context={{ modules } satisfies LayoutContext} />
      </main>
    </div>
  );
}
