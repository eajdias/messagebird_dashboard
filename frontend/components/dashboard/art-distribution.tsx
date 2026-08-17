"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ARTDistributionResponse } from "@/types";

interface ARTDistributionProps {
  data: ARTDistributionResponse | null;
  className?: string;
}

const BUCKET_SEMANTICS = [
  { color: "#22c55e", label: "Ótimo" },
  { color: "#4ade80", label: "Bom" },
  { color: "#86efac", label: "Bom" },
  { color: "var(--chart-3)", label: "Lento" },
  { color: "var(--destructive)", label: "Crítico" },
  { color: "var(--muted-foreground)", label: "N/A" },
] as const;

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return fallback;
}

const EMPTY_BUCKETS: never[] = [];

export const ARTDistribution = memo(function ARTDistribution({ data, className }: ARTDistributionProps) {
  const buckets = data?.buckets ?? EMPTY_BUCKETS;
  const total = safeNum(data?.total);
  const maxCount = useMemo(() => Math.max(...buckets.map((b) => b.count), 1), [buckets]);
  const avgBucketIdx = useMemo(() => {
    if (buckets.length === 0) return -1;
    let cumulative = 0;
    for (let i = 0; i < buckets.length - 1; i++) {
      cumulative += buckets[i].count;
      if (cumulative >= total / 2) return i;
    }
    return buckets.length - 1;
  }, [buckets, total]);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">ART (min)</CardTitle>
          <span className="text-xs text-muted-foreground">{total} chats</span>
        </div>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados de ART no período</p>
        ) : (
          <div className="space-y-2">
            {buckets.map((b, i) => {
              const semantics = BUCKET_SEMANTICS[i] ?? BUCKET_SEMANTICS[5];
              return (
                <div key={b.label} className="space-y-0.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className={`flex items-center gap-1.5 ${i === avgBucketIdx ? "font-semibold text-foreground" : "text-muted-foreground"}`}>
                      {b.label}
                      {i === avgBucketIdx && (
                        <span className="rounded bg-chart-2/20 px-1 py-0.5 text-[10px] font-medium text-chart-2">
                          mediana
                        </span>
                      )}
                    </span>
                    <span className="font-medium tabular-nums">
                      {b.count}
                      <span className="ml-1 text-muted-foreground">({b.pct.toFixed(0)}%)</span>
                    </span>
                  </div>
                  <div className="h-3.5 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${(b.count / maxCount) * 100}%` }}
                      transition={{ duration: 0.8, delay: i * 0.1, ease: "easeOut" }}
                      style={{ background: semantics.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
