"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DOWResponse, MotivesResponse, OccurrencesResponse } from "@/types";

interface DemandBarsProps {
  motives: MotivesResponse | null;
  occurrences: OccurrencesResponse | null;
  dow: DOWResponse | null;
  hideDOW?: boolean;
  className?: string;
}

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

interface HBarListProps {
  title: string;
  data: Array<{ label: string; value: number; pct: number; color: string }>;
  total: number;
  emptyMessage: string;
}

function HBarList({ title, data, total, emptyMessage }: HBarListProps) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <Card variant="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <span className="text-xs text-muted-foreground">Total: {total}</span>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-xs text-muted-foreground">{emptyMessage}</p>
        ) : (
          <div className="space-y-1.5">
            {data.slice(0, 8).map((d, i) => (
              <div key={i} className="group space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="truncate text-muted-foreground group-hover:text-foreground transition-colors">{d.label}</span>
                  <span className="font-medium tabular-nums">
                    {d.value}
                    <span className="ml-1 text-muted-foreground">({d.pct.toFixed(0)}%)</span>
                  </span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
                  <motion.div
                    className="h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(d.value / max) * 100}%` }}
                    transition={{ duration: 0.6, delay: i * 0.05, ease: "easeOut" }}
                    style={{ background: d.color }}
                  />
                </div>
              </div>
            ))}
            {data.length > 8 && (
              <p className="pt-1 text-center text-[10px] text-muted-foreground">
                +{data.length - 8} outros
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const MOTIVE_COLOR = "var(--chart-1)";
const OCCURRENCE_COLOR = "var(--chart-4)";
const DOW_COLOR = "var(--chart-3)";

export const DemandBars = memo(function DemandBars({ motives, occurrences, dow, hideDOW, className }: DemandBarsProps) {
  const motiveItems = (motives?.items ?? []).map((m) => ({
    label: m.label,
    value: safeNum(m.value),
    pct: safeNum(m.pct),
    color: MOTIVE_COLOR,
  }));
  const occurrenceItems = (occurrences?.items ?? []).map((m) => ({
    label: m.label,
    value: safeNum(m.value),
    pct: safeNum(m.pct),
    color: OCCURRENCE_COLOR,
  }));
  const dowItems = (dow?.items ?? []).map((m) => ({
    label: m.label,
    value: safeNum(m.value),
    pct: safeNum(m.pct),
    color: DOW_COLOR,
  }));

  const cols = hideDOW ? "lg:grid-cols-2" : "lg:grid-cols-3";

  return (
    <div className={className}>
      <div className={`grid gap-4 ${cols}`}>
        <HBarList
          title="Top Motivos de Contato"
          data={motiveItems}
          total={motives?.total ?? 0}
          emptyMessage="Sem motivos no período"
        />
        <HBarList
          title="Top Ocorrências"
          data={occurrenceItems}
          total={occurrences?.total ?? 0}
          emptyMessage="Sem ocorrências no período"
        />
        {!hideDOW && (
          <HBarList
            title="Por Dia da Semana"
            data={dowItems}
            total={dow?.total ?? 0}
            emptyMessage="Sem dados no período"
          />
        )}
      </div>
    </div>
  );
});
