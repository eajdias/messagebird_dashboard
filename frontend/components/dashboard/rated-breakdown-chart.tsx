"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EvolutionBucket } from "@/types";

interface RatedBreakdownChartProps {
  data: EvolutionBucket[];
  className?: string;
}

const STACK_ORDER = ["Não avaliados", "Só NPS", "Só Nota", "Ambos"] as const;

const STACK_COLORS: Record<string, string> = {
  Ambos: "var(--chart-2)",
  "Só Nota": "var(--chart-5)",
  "Só NPS": "var(--chart-3)",
  "Não avaliados": "hsl(var(--muted-foreground) / 0.15)",
};

const RADIUS_TOP = [4, 4, 0, 0] as [number, number, number, number];
const RADIUS_FLAT = [0, 0, 0, 0] as [number, number, number, number];

function BreakdownTooltip({ active, payload, label }: Record<string, unknown>) {
  if (!active || !Array.isArray(payload) || payload.length === 0) return null;

  const total = payload.reduce(
    (sum: number, p: { value?: number }) => sum + (p.value ?? 0),
    0,
  );
  const items = payload.filter(
    (p: { value?: number }) => (p.value ?? 0) > 0,
  ) as { color?: string; dataKey?: string; value?: number }[];

  return (
    <div
      style={{
        backgroundColor: "hsl(220 15% 12%)",
        border: "1px solid hsl(var(--border))",
        borderRadius: 8,
        fontSize: 12,
        color: "hsl(var(--foreground))",
        padding: "8px 12px",
      }}
    >
      <p style={{ color: "hsl(var(--muted-foreground))", marginBottom: 6 }}>
        {String(label ?? "")}
      </p>
      {items.map((p) => {
        const pct = total > 0 ? (((p.value ?? 0) / total) * 100).toFixed(1) : "0.0";
        return (
          <div
            key={String(p.dataKey ?? "")}
            style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 2 }}
          >
            <span style={{ color: p.color }}>
              █ {String(p.dataKey ?? "")}
            </span>
            <span style={{ fontFamily: "monospace", fontWeight: 500 }}>
              {p.value}{" "}
              <span style={{ fontSize: 10, color: "hsl(var(--muted-foreground))" }}>
                ({pct}%)
              </span>
            </span>
          </div>
        );
      })}
      <div
        style={{
          borderTop: "1px solid hsl(var(--border))",
          marginTop: 4,
          paddingTop: 4,
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <span style={{ fontWeight: 600 }}>Total</span>
        <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{total}</span>
      </div>
    </div>
  );
}

export function RatedBreakdownChart({ data, className }: RatedBreakdownChartProps) {
  const chartData = data.map((b) => ({
    label: b.label,
    Ambos: b.both_rated_chats,
    "Só NPS": b.nps_rated_chats - b.both_rated_chats,
    "Só Nota": b.rated_chats - b.both_rated_chats,
    "Não avaliados":
      b.total_conversations - b.rated_chats - b.nps_rated_chats + b.both_rated_chats,
  }));

  const hasData = data.some((b) => b.total_conversations > 0);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Cobertura de Avaliações</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <Tooltip content={<BreakdownTooltip />} />
                {STACK_ORDER.map((key, i) => {
                  const isTop = i === STACK_ORDER.length - 1;
                  return (
                    <Bar
                      key={key}
                      dataKey={key}
                      stackId="coverage"
                      fill={STACK_COLORS[key]}
                      radius={isTop ? RADIUS_TOP : RADIUS_FLAT}
                    />
                  );
                })}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
