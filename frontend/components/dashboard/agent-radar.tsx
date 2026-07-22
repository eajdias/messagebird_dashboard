"use client";

import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AgentRankingItem } from "@/types";

interface AgentRadarProps {
  agents: AgentRankingItem[];
  className?: string;
}

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

interface TooltipPayloadEntry {
  name?: string;
  value?: number | string;
  payload?: Record<string, string | number>;
  color?: string;
}

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && !Number.isNaN(v)) return v;
  if (typeof v === "string") {
    const parsed = Number(v);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return fallback;
}

function formatValue(v: unknown): string {
  const n = safeNum(v);
  return n.toFixed(1);
}

function MetricTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-tooltip rounded-lg px-3 py-2 text-xs">
      <p className="font-semibold">{label}</p>
      {payload.map((p, i) => {
        const agentName = String(p.name ?? p.payload?.agent ?? "Agente");
        return (
          <p key={i} className="mt-1" style={{ color: p.color ?? COLORS[i % COLORS.length] }}>
            {agentName}: {formatValue(p.value)}
          </p>
        );
      })}
    </div>
  );
}

export function AgentRadar({ agents, className }: AgentRadarProps) {
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

  const top = agents.slice(0, 4);
  const metrics = [
    { key: "nps", label: "NPS" },
    { key: "sla", label: "SLA %" },
    { key: "art", label: "ART (min)" },
    { key: "rating", label: "Rating" },
    { key: "chats", label: "Chats" },
  ] as const;

  const data = metrics.map((m) => {
    const row: Record<string, number | string> = { metric: m.label };
    top.forEach((a, idx) => {
      let v: number | null = 0;
      switch (m.key) {
        case "nps":
          v = a.nps_score ?? 0;
          break;
        case "sla":
          v = a.sla_compliance_pct ?? 0;
          break;
        case "art":
          v = a.art_avg_minutes ?? 0;
          break;
        case "rating":
          v = a.rating_avg ?? 0;
          break;
        case "chats":
          v = a.total_chats;
          break;
      }
      const safeV = typeof v === "number" && !Number.isNaN(v) ? v : 0;
      row[`agent_${idx}`] = safeV;
    });
    return row;
  });

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-base">Comparativo de Agentes</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[320px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="var(--border)" strokeOpacity={0.4} />
              <PolarAngleAxis
                dataKey="metric"
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, "auto"]}
                tick={{ fill: "var(--muted-foreground)", fontSize: 9 }}
                stroke="var(--border)"
                strokeOpacity={0.3}
              />
              {top.map((a, i) => (
                <Radar
                  key={a.agent_name}
                  name={a.agent_name}
                  dataKey={`agent_${i}`}
                  stroke={COLORS[i % COLORS.length]}
                  fill={COLORS[i % COLORS.length]}
                  fillOpacity={0.18}
                  strokeWidth={2}
                  isAnimationActive={false}
                />
              ))}
              <Tooltip
                content={<MetricTooltip />}
                formatter={(value) => [formatValue(value), ""]}
              />
              <Legend
                iconType="circle"
                wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
