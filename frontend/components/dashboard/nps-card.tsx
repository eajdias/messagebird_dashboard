"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { safeNum } from "@/lib/utils";
import type { NPSBreakdown } from "@/types";

interface NPSCardProps {
  breakdown: NPSBreakdown | null;
  className?: string;
}

export function NPSCard({ breakdown, className }: NPSCardProps) {
  const promoters = safeNum(breakdown?.promoters);
  const neutrals = safeNum(breakdown?.neutrals);
  const detractors = safeNum(breakdown?.detractors);
  const total = safeNum(breakdown?.total);
  const max = Math.max(promoters, neutrals, detractors, 1);
  const realNps = breakdown?.real_nps;

  const rows = [
    { label: "Promotores (9-10)", value: promoters, color: "var(--chart-2)", sub: "Alta satisfação" },
    { label: "Neutros (7-8)", value: neutrals, color: "var(--chart-3)", sub: "Satisfatório" },
    { label: "Detratores (1-6)", value: detractors, color: "var(--destructive)", sub: "Risco de churn" },
  ];

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">NPS</CardTitle>
          <span className="text-xs text-muted-foreground">{total} respostas</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-baseline gap-2">
          <span className="text-3xl font-bold tabular-nums">
            {realNps != null && Number.isFinite(realNps) ? realNps.toFixed(1) : "—"}
          </span>
        </div>
        {total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem avaliações NPS no período</p>
        ) : (
          <div className="space-y-2">
            {rows.map((r) => (
              <div key={r.label} className="space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-medium">{r.label}</span>{" "}
                    <span className="text-muted-foreground">· {r.sub}</span>
                  </div>
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
