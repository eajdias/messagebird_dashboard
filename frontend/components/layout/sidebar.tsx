"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  FileBarChart,
  Settings,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/conversations", label: "Conversas", icon: MessageSquare },
  { href: "/reports", label: "Relatórios", icon: FileBarChart },
  { href: "/agents", label: "Agentes", icon: Users },
  { href: "/settings", label: "Configurações", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-white/5 bg-sidebar/70 text-sidebar-foreground backdrop-blur-xl backdrop-saturate-180 lg:block">
      <div className="flex h-16 items-center gap-2 border-b border-white/5 px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-chart-4 text-primary-foreground text-sm font-bold shadow-md glow-sm [--glow-color:var(--primary)]">
          MB
        </div>
        <span className="bg-gradient-to-r from-primary to-chart-4 bg-clip-text text-lg font-semibold text-transparent">
          MBird
        </span>
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                isActive
                  ? "bg-sidebar-accent text-sidebar-foreground glow-md [--glow-color:var(--primary)]"
                  : "text-muted-foreground hover:bg-white/5 hover:text-sidebar-foreground"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-primary shadow-[0_0_8px_var(--primary)]" />
              )}
              <item.icon
                className={cn(
                  "h-4 w-4 transition-transform group-hover:scale-110",
                  isActive && "text-primary"
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
