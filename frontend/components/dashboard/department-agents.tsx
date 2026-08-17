"use client";

import type { AgentItem } from "@/types";
import { Users } from "lucide-react";

interface DepartmentAgentsProps {
  department: string;
  agents: AgentItem[];
  activeNames?: string[];
  className?: string;
}

function badge(name: string) {
  return (
    <span
      key={name}
      className="inline-flex h-6 items-center rounded-md border border-white/10 bg-white/5 px-2 text-xs backdrop-blur-sm"
    >
      {name}
    </span>
  );
}

export function DepartmentAgents({ department, agents, activeNames, className }: DepartmentAgentsProps) {
  if (!department) return null;
  const filtered = agents
    .filter((a) => a.group === department)
    .filter((a) => !activeNames || activeNames.length === 0 || activeNames.includes(a.name));

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <Users className="mr-0.5 h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-muted-foreground">
          {agents.length === 0
            ? "Carregando agentes..."
            : filtered.length === 0
              ? "Nenhum agente neste período"
              : `${filtered.length} agente(s):`}
        </span>
        {filtered.map((a) => badge(a.name))}
      </div>
    </div>
  );
}
