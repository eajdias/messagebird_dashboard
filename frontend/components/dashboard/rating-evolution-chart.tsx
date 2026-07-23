"use client";

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

export function RatingEvolutionChart({ data, className }: RatingEvolutionChartProps) {
  const chartData = data.map((b) => ({
    label: b.label,
    Avaliados: b.rated_chats,
    "Altas (4-5)": b.high_notes,
    "Baixas (1-2)": b.low_notes,
  }));

  const hasData = data.some((b) => b.rated_chats > 0);
  const maxNotes = Math.max(...data.map((b) => b.high_notes), ...data.map((b) => b.low_notes), 1);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Avaliações (Notas)</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem avaliações no período</p>
        ) : (
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis yAxisId="left" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 10 }}
                  stroke="var(--muted-foreground)"
                  domain={[0, Math.ceil(maxNotes / 10) * 10]}
                />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: 8,
                    fontSize: 12,
                    color: "hsl(var(--foreground))",
                  }}
                  labelStyle={{ color: "hsl(var(--muted-foreground))", marginBottom: 4 }}
                />
                <Bar yAxisId="left" dataKey="Avaliados" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Altas (4-5)"
                  stroke="var(--chart-2)"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "var(--chart-2)" }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Baixas (1-2)"
                  stroke="var(--destructive)"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "var(--destructive)" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
