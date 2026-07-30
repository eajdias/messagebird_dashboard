"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface DowItem {
  label: string;
  value: number;
  pct: number;
  peakHour: string | null;
}

interface DowChartProps {
  items: DowItem[];
  total: number;
  maxValue: number;
  loading?: boolean;
  className?: string;
}

function DowBar({ item, maxValue, index }: { item: DowItem; maxValue: number; index: number }) {
  const pctWidth = maxValue > 0 ? (item.value / maxValue) * 100 : 0;

  const intensity = maxValue > 0 ? item.value / maxValue : 0;
  const isPeak = item.value === maxValue && item.value > 0;
  const bgColor = isPeak
    ? "hsl(262 83% 58%)"
    : `hsl(217 91% ${55 - intensity * 20}%)`;

  return (
    <div className="group space-y-1" title={item.peakHour ? `Pico: ${item.peakHour}` : ""}>
      <div className="flex items-center justify-between text-xs">
        <span className={`w-12 ${isPeak ? "font-semibold text-foreground" : "text-muted-foreground"}`}>{item.label}</span>
        <div className="flex-1 px-2">
          <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
            <motion.div
              className="h-full rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${pctWidth}%` }}
              transition={{ duration: 0.6, delay: 0.1 + index * 0.05, ease: "easeOut" }}
              style={{ backgroundColor: bgColor }}
            />
          </div>
        </div>
        <div className="w-20 text-right">
          <span className={`tabular-nums ${isPeak ? "font-semibold text-foreground" : ""}`}>{item.value}</span>
          <span className="ml-1 text-muted-foreground">({item.pct.toFixed(0)}%)</span>
        </div>
        {isPeak && (
          <span className="ml-1 rounded bg-chart-4/20 px-1 py-0.5 text-[9px] font-semibold text-chart-4">
            pico
          </span>
        )}
      </div>
      {item.peakHour && (
        <p className="pl-14 text-[10px] text-muted-foreground/60 opacity-0 transition-opacity group-hover:opacity-100">
          Pico: {item.peakHour}
        </p>
      )}
    </div>
  );
}

export const DowChart = memo(function DowChart({
  items,
  total,
  maxValue,
  loading = false,
  className,
}: DowChartProps) {
  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Por Dia da Semana</CardTitle>
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
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="space-y-1">
            {items.map((item, i) => (
              <DowBar key={item.label} item={item} maxValue={maxValue} index={i} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
