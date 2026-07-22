"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  Settings,
  Users,
  Download,
  RefreshCw,
  FileText,
  Search,
} from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

const PAGES = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, href: "/", shortcut: "G D" },
  { id: "conversations", label: "Conversas", icon: MessageSquare, href: "/conversations", shortcut: "G C" },
  { id: "agents", label: "Agentes", icon: Users, href: "/agents", shortcut: "G A" },
  { id: "reports", label: "Relatórios", icon: BarChart3, href: "/reports", shortcut: "G R" },
  { id: "settings", label: "Configurações", icon: Settings, href: "/settings", shortcut: "G S" },
];

const ACTIONS = [
  { id: "export", label: "Exportar dados", icon: Download, shortcut: "E" },
  { id: "refresh", label: "Atualizar dados", icon: RefreshCw, shortcut: "R" },
  { id: "report", label: "Gerar relatório", icon: FileText, shortcut: "G R" },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Buscar páginas e ações..." />
      <CommandList>
        <CommandEmpty>Nenhum resultado encontrado.</CommandEmpty>
        <CommandGroup heading="Navegação">
          {PAGES.map((page) => (
            <CommandItem key={page.id} onSelect={() => navigate(page.href)}>
              <page.icon className="mr-2 h-4 w-4" />
              <span>{page.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Ações">
          {ACTIONS.map((action) => (
            <CommandItem key={action.id} onSelect={() => setOpen(false)}>
              <action.icon className="mr-2 h-4 w-4" />
              <span>{action.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
