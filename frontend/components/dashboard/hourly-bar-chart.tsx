"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { HeatmapResponse } from "@/types";

interface HourlyBarChartProps {
  data: HeatmapResponse | null;
  loading?: boolean;
  className?: string;
}

interface HourItem {
  hour: number;
  value: number;
  pct: number;
}

export const HourlyBarChart = memo(function HourlyBarChart({
  data,
  loading = false,
  className,
}: HourlyBarChartProps) {
  const items = useMemo(() => {
    const byHour = new Map<number, number>();
    for (const c of data?.cells ?? []) {
      byHour.set(c.hour, (byHour.get(c.hour) ?? 0) + c.value);
    }
    const total = data?.total ?? 0;
    const arr: HourItem[] = [];
    for (let h = 7; h <= 19; h++) {
      const v = byHour.get(h) ?? 0;
      arr.push({ hour: h, value: v, pct: total > 0 ? (v / total) * 100 : 0 });
    }
    return arr;
  }, [data]);

  const maxValue = Math.max(...items.map((i) => i.value), 1);
  const total = data?.total ?? 0;

  const peakHour = items.reduce((max, i) => (i.value > max.value ? i : max), items[0]);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">% por Horário</CardTitle>
          {loading ? (
            <Skeleton className="h-3 w-16" />
          ) : (
            <span className="text-xs text-muted-foreground">Total: {total}</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-5 w-full" />
            ))}
          </div>
        ) : items.length === 0 || total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="space-y-1">
            {items.map((item, i) => {
              const pctWidth = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
              const intensity = maxValue > 0 ? item.value / maxValue : 0;
              const isPeak = item.hour === peakHour.hour && item.value > 0;
              const bgColor = isPeak
                ? "hsl(262 83% 58%)"
                : `hsl(217 91% ${55 - intensity * 20}%)`;
              return (
                <div key={item.hour} className="group flex items-center gap-1.5 text-xs">
                  <span className={`w-8 tabular-nums ${isPeak ? "font-semibold text-foreground" : "text-muted-foreground"}`}>
                    {item.hour}h
                  </span>
                  <div className="flex-1 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-2.5 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${pctWidth}%` }}
                      transition={{ duration: 0.5, delay: 0.05 + i * 0.03, ease: "easeOut" }}
                      style={{ backgroundColor: bgColor }}
                    />
                  </div>
                  <div className="w-16 text-right tabular-nums">
                    {item.value > 0 && (
                      <>
                        <span className={isPeak ? "font-semibold text-foreground" : ""}>
                          {item.value}
                        </span>
                        <span className="ml-1 text-muted-foreground">
                          ({item.pct.toFixed(0)}%)
                        </span>
                      </>
                    )}
                  </div>
                  {isPeak && (
                    <span className="rounded bg-chart-4/20 px-1 py-0.5 text-[9px] font-semibold text-chart-4">
                      pico
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
