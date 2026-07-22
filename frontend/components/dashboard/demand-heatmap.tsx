"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { HeatmapResponse } from "@/types";

const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function intensityColor(value: number, max: number): string {
  if (max === 0 || value === 0) return "rgba(255,255,255,0.04)";
  const ratio = value / max;
  if (ratio < 0.15) return "rgba(59,130,246,0.18)";
  if (ratio < 0.35) return "rgba(59,130,246,0.32)";
  if (ratio < 0.55) return "rgba(59,130,246,0.50)";
  if (ratio < 0.75) return "rgba(59,130,246,0.70)";
  return "rgba(59,130,246,0.92)";
}

interface DemandHeatmapProps {
  data: HeatmapResponse | null;
  className?: string;
  title?: string;
}

export function DemandHeatmap({ data, className, title = "Mapa de Calor — Chats por Dia/Hora" }: DemandHeatmapProps) {
  const [hover, setHover] = useState<{ day: number; hour: number; value: number; x: number; y: number } | null>(null);

  const grid = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of data?.cells ?? []) {
      m.set(`${c.day}:${c.hour}`, c.value);
    }
    return m;
  }, [data]);

  if (!data || data.total === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sem dados no período</p>
        </CardContent>
      </Card>
    );
  }

  const max = data.max_value;
  const cellSize = 22;
  const gap = 4;
  const labelW = 36;
  const labelH = 20;
  const width = labelW + 24 * (cellSize + gap);
  const height = labelH + 7 * (cellSize + gap);

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="relative inline-block min-w-full">
            <svg width={width} height={height} role="img" aria-label="Heatmap chats por dia e hora">
              {/* Hour labels (top) */}
              {Array.from({ length: 24 }).map((_, h) => (
                <text
                  key={`h-${h}`}
                  x={labelW + h * (cellSize + gap) + cellSize / 2}
                  y={labelH - 6}
                  textAnchor="middle"
                  fontSize={9}
                  fill="var(--muted-foreground)"
                >
                  {h % 3 === 0 ? h : ""}
                </text>
              ))}
              {/* Day labels (left) */}
              {DAYS.map((d, i) => (
                <text
                  key={`d-${i}`}
                  x={labelW - 6}
                  y={labelH + i * (cellSize + gap) + cellSize / 2 + 3}
                  textAnchor="end"
                  fontSize={10}
                  fill="var(--muted-foreground)"
                >
                  {d}
                </text>
              ))}
              {/* Cells */}
              {DAYS.map((_, day) =>
                Array.from({ length: 24 }).map((_, hour) => {
                  const v = grid.get(`${day}:${hour}`) || 0;
                  return (
                    <rect
                      key={`${day}-${hour}`}
                      x={labelW + hour * (cellSize + gap)}
                      y={labelH + day * (cellSize + gap)}
                      width={cellSize}
                      height={cellSize}
                      rx={3}
                      ry={3}
                      fill={intensityColor(v, max)}
                      onMouseEnter={(e) => {
                        const r = (e.target as SVGRectElement).getBoundingClientRect();
                        setHover({
                          day,
                          hour,
                          value: v,
                          x: r.left - r.width / 2,
                          y: r.top,
                        });
                      }}
                      onMouseLeave={() => setHover(null)}
                      style={{ cursor: "pointer" }}
                    />
                  );
                })
              )}
            </svg>
            {hover && (
              <div
                className="glass-tooltip pointer-events-none fixed z-50 rounded-md px-2.5 py-1.5 text-xs shadow-xl"
                style={{ left: hover.x, top: hover.y - 38 }}
              >
                <p className="font-semibold">
                  {DAYS[hover.day]} · {hover.hour}h
                </p>
                <p className="text-muted-foreground">
                  {hover.value} {hover.value === 1 ? "chat" : "chats"}
                </p>
              </div>
            )}
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 text-[10px] text-muted-foreground">
          <span>0</span>
          <div className="flex gap-0.5">
            {[0.18, 0.32, 0.5, 0.7, 0.92].map((v, i) => (
              <span
                key={i}
                className="h-2.5 w-5 rounded-sm"
                style={{ background: `rgba(59,130,246,${v})` }}
              />
            ))}
          </div>
          <span>{max}</span>
          <span className="ml-auto text-muted-foreground">Total: {data.total}</span>
        </div>
      </CardContent>
    </Card>
  );
}
