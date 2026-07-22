"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentRankingItem } from "@/types";

interface AgentComparisonProps {
  agents: AgentRankingItem[];
  className?: string;
}

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

function formatValue(v: unknown): string {
  const n = safeNum(v);
  return n.toFixed(1);
}

interface TooltipPayloadEntry {
  name?: string;
  value?: number | string;
  color?: string;
}

function BarTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadEntry[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-tooltip rounded-md px-2.5 py-1.5 text-xs">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="flex items-center gap-2" style={{ color: p.color }}>
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: p.color }}
          />
          <span className="text-foreground/80">{p.name}:</span>
          <span className="font-medium tabular-nums">{formatValue(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export function AgentComparison({ agents, className }: AgentComparisonProps) {
  if (agents.length === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader>
          <CardTitle className="text-base">Comparativo de Agentes</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sem dados disponíveis</p>
        </CardContent>
      </Card>
    );
  }

  const top = agents.slice(0, 8);
  const data = top.map((a) => ({
    name: a.agent_name.length > 25 ? a.agent_name.slice(0, 22) + "…" : a.agent_name,
    Chats: a.total_chats,
    "SLA %": a.sla_compliance_pct ?? 0,
    "NPS Real": a.nps_score ?? 0,
  }));

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-base">Comparativo de Agentes</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 4, right: 24, left: 0, bottom: 0 }}
            >
              <CartesianGrid stroke="var(--border)" strokeOpacity={0.2} horizontal={false} />
              <XAxis type="number" tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis
                dataKey="name"
                type="category"
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={140}
              />
              <Tooltip content={<BarTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
              <Bar dataKey="Chats" fill="var(--chart-1)" radius={[0, 4, 4, 0]} barSize={14} isAnimationActive={false} />
              <Bar dataKey="SLA %" fill="var(--chart-2)" radius={[0, 4, 4, 0]} barSize={14} isAnimationActive={false} />
              <Bar dataKey="NPS Real" fill="var(--chart-3)" radius={[0, 4, 4, 0]} barSize={14} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
