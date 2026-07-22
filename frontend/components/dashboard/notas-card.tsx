"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { QualityDistribution } from "@/types";

interface NotasCardProps {
  rating: QualityDistribution | null;
  className?: string;
}

const COLORS = [
  "var(--destructive)",
  "var(--destructive)",
  "var(--chart-3)",
  "var(--chart-2)",
  "var(--chart-2)",
];

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return fallback;
}

export function NotasCard({ rating, className }: NotasCardProps) {
  const rows = [1, 2, 3, 4, 5].map((n) => ({
    label: `Nota ${n}`,
    value: safeNum(rating?.counts?.[String(n)] ?? 0),
    color: COLORS[n - 1],
  }));
  const total = safeNum(rating?.total ?? rows.reduce((s, r) => s + r.value, 0));
  const max = Math.max(...rows.map((r) => r.value), 1);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Notas (1-5)</CardTitle>
          <span className="text-xs text-muted-foreground">{total} avaliações</span>
        </div>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem notas no período</p>
        ) : (
          <div className="space-y-2">
            {rows.map((r) => (
              <div key={r.label} className="space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{r.label}</span>
                  <span className="font-medium tabular-nums">
                    {r.value}{" "}
                    <span className="text-muted-foreground">
                      ({total > 0 ? ((r.value / total) * 100).toFixed(0) : 0}%)
                    </span>
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${(r.value / max) * 100}%`,
                      background: r.color,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
