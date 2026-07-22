"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
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

interface DataPoint {
  hora: string;
  chats: number;
  pct: number;
  color: string;
}

function Tooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: DataPoint }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="glass-tooltip rounded-md px-2.5 py-1.5 text-xs">
      <p className="font-medium">
        {d.chats} {d.chats === 1 ? "chat" : "chats"} ({d.pct.toFixed(1)}%)
      </p>
    </div>
  );
}

export function HourlyChart({ heatmap, className }: HourlyChartProps) {
  const data = useMemo(() => {
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
    const arr: DataPoint[] = [];
    for (let h = 7; h <= 19; h++) {
      const v = byHour.get(h) ?? 0;
      arr.push({ hora: `${h}h`, chats: v, pct: tot > 0 ? (v / tot) * 100 : 0, color: PEAK_COLOR });
    }
    if (out > 0) {
      arr.push({ hora: "Fora do\nexpediente", chats: out, pct: tot > 0 ? (out / tot) * 100 : 0, color: OUT_COLOR });
    }
    return { arr, total: tot };
  }, [heatmap]);

  const total = data.total;

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
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.arr} margin={{ top: 16, right: 4, left: 0, bottom: 12 }}>
                <CartesianGrid stroke="var(--border)" strokeOpacity={0.15} vertical={false} />
                <XAxis
                  dataKey="hora"
                  tick={{ fill: "var(--muted-foreground)", fontSize: 9 }}
                  interval={0}
                  axisLine={false}
                  tickLine={false}
                  height={32}
                />
                <YAxis hide />
                <RechartsTooltip content={<Tooltip />} cursor={false} />
                <Bar dataKey="chats" radius={[3, 3, 0, 0]} isAnimationActive={false} barSize={18}>
                  {data.arr.map((d, i) => (
                    <Cell key={i} fill={d.color} />
                  ))}
                  <LabelList
                    dataKey="pct"
                    position="top"
                    formatter={((v: number) => `${v > 0 ? v.toFixed(0) : ""}%`) as unknown as undefined}
                    fill="var(--muted-foreground)"
                    fontSize={8}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
