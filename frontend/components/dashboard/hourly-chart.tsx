"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HeatmapResponse } from "@/types";

interface HourlyChartProps {
  heatmap: HeatmapResponse | null;
  className?: string;
}

/**
 * Business hours definition: { validHours: set, label }
 *
 * - Mon–Thu: 7h–19h (covering 7:30–20:00)
 * - Fri: 7h–18h (covering 7:30–19:00)
 * - Sat: 8h–11h (covering 8:00–12:00)
 * - Sun: none (all out of hours)
 */
const BUSINESS_HOURS: Record<number, Set<number>> = {
  0: new Set([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
  1: new Set([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
  2: new Set([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
  3: new Set([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]),
  4: new Set([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]),
  5: new Set([8, 9, 10, 11]),
};

const PEAK_COLOR = "var(--chart-1)";
const OUT_COLOR = "var(--destructive)";

interface TooltipPayloadEntry {
  value?: number;
}

function Tooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadEntry[]; label?: string }) {
  if (!active || !payload?.length) return null;
  const v = payload[0]?.value ?? 0;
  return (
    <div className="glass-tooltip rounded-md px-2.5 py-1.5 text-xs">
      <p className="font-medium">{v} {v === 1 ? "chat" : "chats"}</p>
    </div>
  );
}

export function HourlyChart({ heatmap, className }: HourlyChartProps) {
  const { inHours, outCount, total } = useMemo(() => {
    const byHour = new Map<number, number>();
    for (let h = 7; h <= 19; h++) byHour.set(h, 0);
    let out = 0;
    let tot = 0;
    for (const c of heatmap?.cells ?? []) {
      tot += c.value;
      if (BUSINESS_HOURS[c.day]?.has(c.hour)) {
        byHour.set(c.hour, (byHour.get(c.hour) ?? 0) + c.value);
      } else {
        out += c.value;
      }
    }
    return { inHours: byHour, outCount: out, total: tot };
  }, [heatmap]);

  const data = useMemo(() => {
    const arr: { hora: string; chats: number; color: string }[] = [];
    for (let h = 7; h <= 19; h++) {
      arr.push({ hora: `${h}h`, chats: inHours.get(h) ?? 0, color: PEAK_COLOR });
    }
    if (outCount > 0) {
      arr.push({ hora: "Fora do\nexpediente", chats: outCount, color: OUT_COLOR });
    }
    return arr;
  }, [inHours, outCount]);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Atendimentos por Horário</CardTitle>
          <span className="text-xs text-muted-foreground">{total} chats</span>
        </div>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 12 }}>
                <CartesianGrid stroke="var(--border)" strokeOpacity={0.15} vertical={false} />
                <XAxis
                  dataKey="hora"
                  tick={{ fill: "var(--muted-foreground)", fontSize: 9 }}
                  interval={0}
                  axisLine={false}
                  tickLine={false}
                  height={30}
                />
                <YAxis hide />
                <RechartsTooltip content={<Tooltip />} cursor={false} />
                <Bar dataKey="chats" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                  {data.map((d, i) => (
                    <Cell key={i} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
