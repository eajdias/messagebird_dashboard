"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DepartmentsResponse } from "@/types";

interface DepartmentChartProps {
  data: DepartmentsResponse | null;
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

interface TooltipPayloadEntry {
  name: string;
  value: number;
  color?: string;
  dataKey?: string;
  payload?: { name: string };
}

function DeptTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadEntry[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-tooltip rounded-md px-2.5 py-1.5 text-xs">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="flex items-center gap-2" style={{ color: p.color }}>
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: p.color }}
          />
          <span className="text-foreground/80">{p.name}:</span>
          <span className="font-medium tabular-nums">{safeNum(p.value).toFixed(1)}</span>
        </p>
      ))}
    </div>
  );
}

export function DepartmentChart({ data, className }: DepartmentChartProps) {
  if (!data || data.items.length === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader>
          <CardTitle className="text-base">Por Departamento</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sem dados no período</p>
        </CardContent>
      </Card>
    );
  }

  const rows = data.items.map((d) => ({
    name: d.name,
    ART: d.art_avg,
    SLA: d.sla_pct,
    Retornantes: d.pct_returning,
    NPS: d.nps_real,
    Chats: d.chats,
    avg_rating: d.avg_rating,
  }));

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Por Departamento</CardTitle>
          <span className="text-xs text-muted-foreground">Total: {data.total_chats} chats</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeOpacity={0.2} vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
                angle={-15}
                textAnchor="end"
                height={50}
              />
              <YAxis
                tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
              />
              <Tooltip content={<DeptTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
              <Legend
                iconType="circle"
                wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
              />
              <Bar dataKey="ART" name="ART (min)" fill="var(--chart-3)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="SLA" name="SLA %" fill="var(--chart-2)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="Retornantes" name="% Retornantes" fill="var(--chart-4)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="NPS" name="NPS Real" fill="var(--chart-1)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
