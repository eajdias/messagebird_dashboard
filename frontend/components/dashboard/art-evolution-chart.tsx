"use client";

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

export function ARTEvolutionChart({ data, className }: ARTEvolutionChartProps) {
  const chartData = data.map((b) => ({
    label: b.label,
    "0–5 min": b.art_bucket_0_5,
    "5–10 min": b.art_bucket_5_10,
    "10–30 min": b.art_bucket_10_30,
    "30 min+": b.art_bucket_30_60 + b.art_bucket_60_120 + b.art_bucket_120_plus,
  }));

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
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(220 15% 12%)",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: 8,
                    fontSize: 12,
                    color: "hsl(var(--foreground))",
                  }}
                  labelStyle={{ color: "hsl(var(--muted-foreground))", marginBottom: 4 }}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} iconType="line" />
                {BANDS.map((band) => (
                  <Line
                    key={band.key}
                    type="monotone"
                    dataKey={band.key}
                    stroke={band.color}
                    strokeWidth={2}
                    dot={{ r: 2, fill: band.color }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
