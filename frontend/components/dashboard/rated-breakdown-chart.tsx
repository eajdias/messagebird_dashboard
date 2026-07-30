"use client";

import { memo, useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvolutionBucket } from "@/types";

interface RatedBreakdownChartProps {
  data: EvolutionBucket[];
  className?: string;
}

const COVERAGE_SEGMENTS = [
  { key: "Ambos", label: "Ambos (NPS + Nota)", color: "#22c55e" },
  { key: "Só Nota", label: "Só Nota", color: "#a855f7" },
  { key: "Só NPS", label: "Só NPS", color: "#f59e0b" },
  { key: "Sem avaliação", label: "Sem avaliação", color: "#94a3b8" },
] as const;

function DonutTooltip({ active, payload }: Record<string, unknown>) {
  if (!active || !Array.isArray(payload) || payload.length === 0) return null;
  const item = payload[0] as { name?: string; value?: number; payload?: { pct?: number; total?: number } };
  if (!item) return null;
  return (
    <div className="glass-tooltip rounded-lg px-4 py-3 text-xs shadow-xl backdrop-blur-md">
      <p className="mb-1.5 font-bold text-foreground">{String(item.name ?? "")}</p>
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold text-foreground">{item.value}</span>
        <span className="text-muted-foreground">chats</span>
        {item.payload?.pct != null && (
          <span className="rounded bg-primary/15 px-1.5 py-0.5 text-xs font-semibold text-primary">
            {item.payload.pct.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}

const RADIAN = Math.PI / 180;

function renderCustomLabel(props: { cx?: number; cy?: number; midAngle?: number; innerRadius?: number; outerRadius?: number; percent?: number }) {
  const cx = props.cx ?? 0;
  const cy = props.cy ?? 0;
  const midAngle = props.midAngle ?? 0;
  const innerRadius = props.innerRadius ?? 0;
  const outerRadius = props.outerRadius ?? 0;
  const percent = props.percent ?? 0;
  if (percent < 0.04) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export const RatedBreakdownChart = memo(function RatedBreakdownChart({ data, className }: RatedBreakdownChartProps) {
  const totalConversations = data.reduce((s, b) => s + b.total_conversations, 0);

  const totals = useMemo(() => {
    let ambas = 0, soNota = 0, soNps = 0, sem = 0;
    for (const b of data) {
      ambas += b.both_rated_chats;
      soNota += Math.max(0, b.rated_chats - b.both_rated_chats);
      soNps += Math.max(0, b.nps_rated_chats - b.both_rated_chats);
      sem += Math.max(0, b.total_conversations - b.rated_chats - b.nps_rated_chats + b.both_rated_chats);
    }
    return { ambas, soNota, soNps, sem };
  }, [data]);

  const chartData = useMemo(() => {
    const total = totals.ambas + totals.soNota + totals.soNps + totals.sem;
    return COVERAGE_SEGMENTS.map((seg) => {
      const val = seg.key === "Ambos" ? totals.ambas
        : seg.key === "Só Nota" ? totals.soNota
        : seg.key === "Só NPS" ? totals.soNps
        : totals.sem;
      return {
        name: seg.label,
        value: val,
        pct: total > 0 ? (val / total) * 100 : 0,
        color: seg.color,
        total,
      };
    }).filter((d) => d.value > 0);
  }, [totals]);

  const hasData = totalConversations > 0;
  const ratedPct = totalConversations > 0
    ? ((totals.ambas + totals.soNota + totals.soNps) / totalConversations * 100)
    : 0;

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Cobertura de Avaliações</CardTitle>
          {hasData && (
            <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-semibold text-primary">
              {ratedPct.toFixed(1)}% avaliados
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="flex items-center gap-3">
            <div className="flex flex-col gap-1.5 text-xs shrink-0 w-[130px]">
              {chartData.map((d) => (
                <div key={d.name} className="space-y-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ background: d.color }} />
                    <span className="text-muted-foreground truncate">{d.name}</span>
                  </div>
                  <div className="pl-4 flex items-center justify-between">
                    <span className="tabular-nums font-medium">{d.value}</span>
                    <span className="text-muted-foreground tabular-nums">{d.pct.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="h-[280px] flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius="35%"
                    outerRadius="85%"
                    paddingAngle={2}
                    dataKey="value"
                    nameKey="name"
                    labelLine={false}
                    label={renderCustomLabel}
                    animationDuration={1000}
                    animationEasing="ease-out"
                  >
                    {chartData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} stroke="var(--background)" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip content={<DonutTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});