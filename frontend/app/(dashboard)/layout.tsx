"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/topbar";
import { PageTransition } from "@/components/layout/page-transition";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, loading, user } = useAuth();
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const userRole = user?.role ?? "agent";

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  useKeyboardShortcuts([
    { keys: ["g", "d"], handler: useCallback(() => router.push("/"), [router]), description: "Go to Dashboard" },
    { keys: ["g", "c"], handler: useCallback(() => router.push("/conversations"), [router]), description: "Go to Conversas" },
    { keys: ["g", "a"], handler: useCallback(() => router.push("/agents"), [router]), description: "Go to Agentes" },
    { keys: ["g", "r"], handler: useCallback(() => router.push("/reports"), [router]), description: "Go to Relatorios" },
    { keys: ["g", "s"], handler: useCallback(() => router.push("/settings"), [router]), description: "Go to Settings" },
    { keys: ["r"], handler: useCallback(() => { window.location.reload(); }, []), description: "Refresh page" },
  ]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="relative flex h-screen overflow-hidden">
      <div className="animated-bg pointer-events-none absolute inset-0 -z-10" aria-hidden="true" />
      <Sidebar collapsed={sidebarCollapsed} role={userRole} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar sidebarCollapsed={sidebarCollapsed} onToggleSidebar={() => setSidebarCollapsed((v) => !v)} />
        <main className="flex-1 overflow-y-auto px-3 py-4 sm:px-4 md:px-6">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
}
