"use client";

import { memo, useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvolutionBucket } from "@/types";

interface NPSEvolutionChartProps {
  data: EvolutionBucket[];
  className?: string;
}

function NPSTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !Array.isArray(payload) || payload.length === 0) return null;
  const totalNPS = payload.reduce((sum: number, p: Record<string, unknown>) => {
    const dk = String(p.dataKey ?? "");
    if (dk === "Avaliados NPS") return sum + Number(p.value ?? 0);
    return sum;
  }, 0);
  return (
    <div className="glass-tooltip rounded-lg px-4 py-3 text-xs shadow-xl backdrop-blur-md">
      <p className="mb-2 font-bold text-foreground">{String(label ?? "")}</p>
      {payload.map((p: Record<string, unknown>) => {
        if (p.value == null || p.value === 0) return null;
        const dk = String(p.dataKey ?? "");
        const val = Number(p.value);
        const pct = dk === "Avaliados NPS" && totalNPS > 0 ? ((val / totalNPS) * 100).toFixed(1) : null;
        return (
          <div key={dk} className="mb-1 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full" style={{ background: String(p.color ?? "") }} />
              <span className="text-muted-foreground">{dk}</span>
            </div>
            <div className="flex items-center gap-1.5 tabular-nums font-medium">
              <span>{dk.includes("Médio") ? val.toFixed(1) : val}</span>
              {pct && <span className="text-muted-foreground">({pct}%)</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export const NPSEvolutionChart = memo(function NPSEvolutionChart({ data, className }: NPSEvolutionChartProps) {
  const chartData = useMemo(() => data.map((b) => ({
    label: b.label,
    "Avaliados NPS": b.nps_rated_chats,
    "NPS Médio": b.nps_score,
  })), [data]);

  const hasData = data.some((b) => b.nps_rated_chats > 0);
  const npsMin = Math.min(...data.map((b) => b.nps_score ?? 100).filter((v) => v !== 100), 0);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">NPS</CardTitle>
      </CardHeader>
      <CardContent className="p-2 sm:p-4">
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem avaliações NPS no período</p>
        ) : (
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="npsBarGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-3)" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="var(--chart-3)" stopOpacity={0.4} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.4} />
                <XAxis dataKey="label" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                <YAxis yAxisId="left" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 9 }}
                  stroke="var(--muted-foreground)"
                  domain={[Math.floor(npsMin / 10) * 10, 100]}
                />
                <Bar
                  yAxisId="left"
                  dataKey="Avaliados NPS"
                  fill="url(#npsBarGrad)"
                  radius={[4, 4, 0, 0]}
                  animationDuration={1200}
                  animationEasing="ease-out"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="NPS Médio"
                  stroke="var(--chart-2)"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "var(--chart-2)", strokeWidth: 2, stroke: "hsl(var(--background))" }}
                  activeDot={{ r: 5, stroke: "var(--chart-2)", strokeWidth: 2, fill: "hsl(var(--background))" }}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
                <Tooltip content={<NPSTooltip />} cursor={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
