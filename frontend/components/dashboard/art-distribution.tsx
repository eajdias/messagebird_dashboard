"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ARTDistributionResponse } from "@/types";

interface ARTDistributionProps {
  data: ARTDistributionResponse | null;
  className?: string;
}

const BUCKET_COLORS = [
  "var(--chart-5)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-2)",
  "var(--destructive)",
  "var(--muted-foreground)",
] as const;

function safeNum(v: unknown, fallback = 0): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return fallback;
}

const EMPTY_BUCKETS: never[] = [];

export function ARTDistribution({ data, className }: ARTDistributionProps) {
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
            {buckets.map((b, i) => (
              <div key={b.label} className="space-y-0.5">
                <div className="flex items-center justify-between text-xs">
                  <span className={i === avgBucketIdx ? "font-medium" : "text-muted-foreground"}>
                    {b.label}
                    {i === avgBucketIdx && <span className="ml-1 text-muted-foreground">· mediana</span>}
                  </span>
                  <span className="font-medium tabular-nums">
                    {b.count}{" "}
                    <span className="text-muted-foreground">({b.pct.toFixed(0)}%)</span>
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${(b.count / maxCount) * 100}%`,
                      background: BUCKET_COLORS[i] ?? BUCKET_COLORS[5],
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
