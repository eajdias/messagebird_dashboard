"use client";

import { memo, useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvolutionBucket } from "@/types";

interface ARTEvolutionChartProps {
  data: EvolutionBucket[];
  className?: string;
}

const BANDS = [
  { key: "0–5 min", color: "var(--chart-1)" },
  { key: "5–10 min", color: "var(--chart-2)" },
  { key: "10–30 min", color: "var(--chart-3)" },
  { key: "30 min+", color: "var(--destructive)" },
] as const;

function ARTTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !Array.isArray(payload) || payload.length === 0) return null;
  return (
    <div className="glass-tooltip rounded-lg px-3 py-2 text-xs shadow-xl backdrop-blur-md">
      <p className="mb-1.5 font-semibold text-foreground">{String(label ?? "")}</p>
      {payload.map((p: Record<string, unknown>) => {
        if (p.value == null || p.value === 0) return null;
        const dk = String(p.dataKey ?? "");
        return (
          <div key={dk} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: String(p.color ?? "") }} />
            <span className="text-muted-foreground">{dk}:</span>
            <span className="font-medium tabular-nums">{String(p.value)}</span>
          </div>
        );
      })}
    </div>
  );
}

export const ARTEvolutionChart = memo(function ARTEvolutionChart({ data, className }: ARTEvolutionChartProps) {
  const chartData = useMemo(() => data.map((b) => ({
    label: b.label,
    "0–5 min": b.art_bucket_0_5,
    "5–10 min": b.art_bucket_5_10,
    "10–30 min": b.art_bucket_10_30,
    "30 min+": b.art_bucket_30_60 + b.art_bucket_60_120 + b.art_bucket_120_plus,
  })), [data]);

  const hasData = data.some(
    (b) =>
      b.art_bucket_0_5 > 0 ||
      b.art_bucket_5_10 > 0 ||
      b.art_bucket_10_30 > 0 ||
      b.art_bucket_30_60 > 0 ||
      b.art_bucket_60_120 > 0 ||
      b.art_bucket_120_plus > 0,
  );

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Distribuição ART (min)</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem dados de ART no período</p>
        ) : (
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.4} />
                <XAxis dataKey="label" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                <Tooltip content={<ARTTooltip />} cursor={false} />
                <Legend wrapperStyle={{ fontSize: 9 }} iconType="line" />
                {BANDS.map((band) => (
                  <Line
                    key={band.key}
                    type="monotone"
                    dataKey={band.key}
                    stroke={band.color}
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: band.color, strokeWidth: 2, stroke: "hsl(var(--background))" }}
                    activeDot={{ r: 5, stroke: band.color, strokeWidth: 2, fill: "hsl(var(--background))" }}
                    animationDuration={1200}
                    animationEasing="ease-out"
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
});
