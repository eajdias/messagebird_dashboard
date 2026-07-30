"use client";

import { memo } from "react";
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

interface RatingEvolutionChartProps {
  data: EvolutionBucket[];
  className?: string;
}

function RatingTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !Array.isArray(payload) || payload.length === 0) return null;
  const total = payload.reduce((sum: number, p: Record<string, unknown>) => {
    const dk = String(p.dataKey ?? "");
    if (dk === "Avaliados") return sum;
    return sum + (Number(p.value ?? 0));
  }, 0);
  return (
    <div className="glass-tooltip rounded-lg px-4 py-3 text-xs shadow-xl backdrop-blur-md">
      <p className="mb-2 font-bold text-foreground">{String(label ?? "")}</p>
      {payload.map((p: Record<string, unknown>) => {
        if (p.value == null) return null;
        const dk = String(p.dataKey ?? "");
        const val = Number(p.value);
        const pct = dk !== "Avaliados" && total > 0 ? ((val / total) * 100).toFixed(1) : null;
        return (
          <div key={dk} className="mb-1 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full" style={{ background: String(p.color ?? "") }} />
              <span className="text-muted-foreground">{dk}</span>
            </div>
            <div className="flex items-center gap-1.5 tabular-nums font-medium">
              <span>{val}</span>
              {pct && <span className="text-muted-foreground">({pct}%)</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export const RatingEvolutionChart = memo(function RatingEvolutionChart({ data, className }: RatingEvolutionChartProps) {
  const chartData = data.map((b) => ({
    label: b.label,
    Avaliados: b.rated_chats,
    "Altas (4-5)": b.high_notes,
    Neutros: b.neutral_notes ?? 0,
    "Baixas (1-2)": b.low_notes,
  }));

  const hasData = data.some((b) => b.rated_chats > 0);
  const maxNotes = Math.max(
    ...data.map((b) => b.high_notes),
    ...data.map((b) => b.neutral_notes ?? 0),
    ...data.map((b) => b.low_notes),
    1,
  );

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Avaliações (Notas)</CardTitle>
      </CardHeader>
      <CardContent className="p-2 sm:p-4">
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem avaliações no período</p>
        ) : (
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="ratingBarGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0.4} />
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
                  domain={[0, Math.ceil(maxNotes / 10) * 10]}
                />
                <Tooltip content={<RatingTooltip />} cursor={false} />
                <Bar
                  yAxisId="left"
                  dataKey="Avaliados"
                  fill="url(#ratingBarGrad)"
                  radius={[4, 4, 0, 0]}
                  animationDuration={1200}
                  animationEasing="ease-out"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Altas (4-5)"
                  stroke="#22c55e"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#22c55e", strokeWidth: 2, stroke: "hsl(var(--background))" }}
                  activeDot={{ r: 5, stroke: "#22c55e", strokeWidth: 2, fill: "hsl(var(--background))" }}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Neutros"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  dot={{ r: 2, fill: "#f59e0b", strokeWidth: 1.5, stroke: "hsl(var(--background))" }}
                  activeDot={{ r: 4, stroke: "#f59e0b", strokeWidth: 2, fill: "hsl(var(--background))" }}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Baixas (1-2)"
                  stroke="var(--destructive)"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "var(--destructive)", strokeWidth: 2, stroke: "hsl(var(--background))" }}
                  activeDot={{ r: 5, stroke: "var(--destructive)", strokeWidth: 2, fill: "hsl(var(--background))" }}
                  animationDuration={1500}
                  animationEasing="ease-in-out"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
