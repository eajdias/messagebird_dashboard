"use client";

import {
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface NPSGaugeProps {
  value: number | null;
  className?: string;
}

function colorForScore(score: number): string {
  if (score >= 75) return "var(--chart-2)";
  if (score >= 50) return "var(--chart-1)";
  if (score >= 0) return "var(--chart-3)";
  return "var(--destructive)";
}

function labelForScore(score: number): string {
  if (score >= 75) return "Excelente";
  if (score >= 50) return "Muito bom";
  if (score >= 0) return "Neutro";
  return "Crítico";
}

export function NPSGauge({ value, className }: NPSGaugeProps) {
  const score = value ?? 0;
  const color = colorForScore(score);
  const label = value == null ? "Sem dados" : labelForScore(score);
  const Icon = score >= 50 ? TrendingUp : score >= 0 ? Minus : TrendingDown;

  const data = [{ name: "NPS", value: Math.max(-100, Math.min(100, score)), fill: color }];

  return (
    <Card variant="glass" className={cn("relative overflow-hidden", className)}>
      <span
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          background: `radial-gradient(ellipse at top, ${color.replace("var(--", "rgb(from var(--").replace(")", ") r g b / 0.18")}, transparent 60%)`,
        }}
      />
      <CardHeader className="relative">
        <CardTitle className="text-base">NPS</CardTitle>
      </CardHeader>
      <CardContent className="relative flex flex-col items-center justify-center">
        <div className="relative h-[180px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              data={data}
              startAngle={90}
              endAngle={-270}
              innerRadius="70%"
              outerRadius="100%"
              cy="50%"
            >
              <PolarAngleAxis type="number" domain={[-100, 100]} tick={false} />
              <RadialBar
                dataKey="value"
                cornerRadius={10}
                fill={color}
                background={{ fill: "var(--muted)" } as never}
              />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold tabular-nums">{value?.toFixed(1) ?? "—"}</span>
            <span
              className="mt-1 flex items-center gap-1 text-xs font-medium"
              style={{ color }}
            >
              <Icon className="h-3 w-3" />
              {label}
            </span>
          </div>
        </div>
        <div className="mt-2 flex w-full justify-between text-[10px] text-muted-foreground">
          <span>-100</span>
          <span>0</span>
          <span>+100</span>
        </div>
      </CardContent>
    </Card>
  );
}
