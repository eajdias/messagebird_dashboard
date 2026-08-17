"use client";

import { memo, useCallback, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HeatmapResponse } from "@/types";

interface HeatmapGridProps {
  data: HeatmapResponse | null;
  className?: string;
}

const DOW_LABELS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const HOURS = Array.from({ length: 13 }, (_, i) => i + 7);

const CELL_PADDING = 1;
const LABEL_WIDTH = 28;
const LABEL_HEIGHT = 16;
const CELL_MIN = 26;

function heatColor(value: number, max: number): string {
  if (max === 0 || value === 0) return "#f0f4ff";
  const t = Math.min(value / max, 1);
  if (t < 0.25) {
    const s = t / 0.25;
    const r = Math.round(219 + (147 - 219) * s);
    const g = Math.round(234 + (197 - 234) * s);
    const b = Math.round(251 + (251 - 251) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  if (t < 0.5) {
    const s = (t - 0.25) / 0.25;
    const r = Math.round(147 + (251 - 147) * s);
    const g = Math.round(197 + (191 - 197) * s);
    const b = Math.round(251 + (121 - 251) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  if (t < 0.75) {
    const s = (t - 0.5) / 0.25;
    const r = Math.round(251 + (251 - 251) * s);
    const g = Math.round(191 + (120 - 191) * s);
    const b = Math.round(121 + (68 - 121) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  const s = (t - 0.75) / 0.25;
  const r = Math.round(251 + (239 - 251) * s);
  const g = Math.round(120 + (68 - 120) * s);
  const b = Math.round(68 + (68 - 68) * s);
  return `rgb(${r} ${g} ${b})`;
}

function heatColorDark(value: number, max: number): string {
  if (max === 0 || value === 0) return "rgba(30, 58, 95, 0.3)";
  const t = Math.min(value / max, 1);
  if (t < 0.25) {
    const s = t / 0.25;
    const r = Math.round(30 + (56 - 30) * s);
    const g = Math.round(58 + (116 - 58) * s);
    const b = Math.round(95 + (189 - 95) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  if (t < 0.5) {
    const s = (t - 0.25) / 0.25;
    const r = Math.round(56 + (251 - 56) * s);
    const g = Math.round(116 + (191 - 116) * s);
    const b = Math.round(189 + (121 - 189) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  if (t < 0.75) {
    const s = (t - 0.5) / 0.25;
    const r = Math.round(251 + (251 - 251) * s);
    const g = Math.round(191 + (120 - 191) * s);
    const b = Math.round(121 + (68 - 121) * s);
    return `rgb(${r} ${g} ${b})`;
  }
  const s = (t - 0.75) / 0.25;
  const r = Math.round(251 + (239 - 251) * s);
  const g = Math.round(120 + (68 - 120) * s);
  const b = Math.round(68 + (68 - 68) * s);
  return `rgb(${r} ${g} ${b})`;
}

interface TooltipData {
  day: number;
  hour: number;
  value: number;
  x: number;
  y: number;
}

export const HeatmapGrid = memo(function HeatmapGrid({ data, className }: HeatmapGridProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  const maxValue = useMemo(() => {
    if (!data?.cells?.length) return 0;
    return Math.max(...data.cells.map((c) => c.value), 1);
  }, [data]);

  const cellMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const c of data?.cells ?? []) {
      map.set(`${c.day}-${c.hour}`, c.value);
    }
    return map;
  }, [data]);

  const gridWidth = HOURS.length * CELL_MIN;
  const gridHeight = DOW_LABELS.length * CELL_MIN;
  const svgWidth = LABEL_WIDTH + gridWidth + 16;
  const svgHeight = LABEL_HEIGHT + gridHeight + 16;

  const handleMouseMove = useCallback(
    (day: number, hour: number, value: number, e: React.MouseEvent<SVGRectElement>) => {
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      setTooltip({
        day,
        hour,
        value,
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    },
    [],
  );

  const handleMouseLeave = useCallback(() => setTooltip(null), []);

  const total = data?.total ?? 0;
  const activeDays = useMemo(() => {
    const days = new Set<number>();
    for (const c of data?.cells ?? []) {
      if (c.value > 0) days.add(c.day);
    }
    return days;
  }, [data]);

  const isDark = typeof document !== "undefined" && document.documentElement.classList.contains("dark");
  const colorFn = isDark ? heatColorDark : heatColor;

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Mapa de Calor</CardTitle>
          <span className="text-xs text-muted-foreground">{total} chats</span>
        </div>
      </CardHeader>
      <CardContent>
        {!data?.cells?.length || total === 0 ? (
          <p className="text-xs text-muted-foreground">Sem dados no período</p>
        ) : (
          <div className="relative">
            <svg
              ref={svgRef}
              viewBox={`0 0 ${svgWidth} ${svgHeight}`}
              className="w-full"
              style={{ fontFamily: "var(--font-sans)" }}
              onMouseLeave={handleMouseLeave}
            >
              {HOURS.map((h, i) => (
                <text
                  key={h}
                  x={LABEL_WIDTH + i * CELL_MIN + CELL_MIN / 2}
                  y={LABEL_HEIGHT - 6}
                  textAnchor="middle"
                  fontSize={9}
                  fill="var(--muted-foreground)"
                  fontFamily="var(--font-sans)"
                >
                  {h}h
                </text>
              ))}

              {DOW_LABELS.map((dayLabel, dayIdx) => (
                <g key={dayIdx}>
                  <text
                    x={LABEL_WIDTH - 6}
                    y={LABEL_HEIGHT + dayIdx * CELL_MIN + CELL_MIN / 2 + 3}
                    textAnchor="end"
fontSize={9}
                    fill={activeDays.has(dayIdx) ? "var(--foreground)" : "var(--muted-foreground)"}
                    fontFamily="var(--font-sans)"
                    fontWeight={activeDays.has(dayIdx) ? 600 : 400}
                  >
                    {dayLabel}
                  </text>
                  {HOURS.map((hour, hourIdx) => {
                    const value = cellMap.get(`${dayIdx}-${hour}`) ?? 0;
                    const fill = colorFn(value, maxValue);
                    const x = LABEL_WIDTH + hourIdx * CELL_MIN + CELL_PADDING;
                    const y = LABEL_HEIGHT + dayIdx * CELL_MIN + CELL_PADDING;
                    const size = CELL_MIN - CELL_PADDING * 2;
                    return (
                      <rect
                        key={hour}
                        x={x}
                        y={y}
                        width={size}
                        height={size}
                        rx={3}
                        fill={fill}
                        stroke={value > 0 ? "rgba(0,0,0,0.08)" : "var(--border)"}
                        strokeWidth={value > 0 ? 0.8 : 0.3}
                        onMouseMove={(e) => handleMouseMove(dayIdx, hour, value, e)}
                        onMouseLeave={handleMouseLeave}
                        style={{ cursor: "pointer", transition: "opacity 0.15s" }}
                        opacity={value > 0 ? 1 : 0.5}
                      />
                    );
                  })}
                </g>
              ))}
            </svg>

            <div className="mt-2 flex items-center justify-center gap-1.5 text-[9px] text-muted-foreground">
              <span>Menos</span>
              <div className="flex gap-px">
                {[0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1].map((t) => (
                  <div
                    key={t}
                    className="h-2.5 w-2.5 rounded-sm"
                    style={{ backgroundColor: colorFn(Math.round(maxValue * t), maxValue) }}
                  />
                ))}
              </div>
              <span>Mais</span>
            </div>

            {tooltip && (
              <div
                className="pointer-events-none absolute z-50 rounded-xl border border-border/50 bg-card/95 px-4 py-3 text-sm shadow-2xl backdrop-blur-md"
                style={{
                  left: Math.min(tooltip.x, (svgRef.current?.getBoundingClientRect().width ?? 400) - 200),
                  top: Math.max(0, tooltip.y - 80),
                  minWidth: 180,
                }}
              >
                <div className="mb-1.5 font-bold text-foreground">
                  {DOW_LABELS[tooltip.day]}, {tooltip.hour}h – {tooltip.hour + 1}h
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <span className="text-lg font-bold text-foreground">{tooltip.value}</span>
                  <span>chats</span>
                  {tooltip.value > 0 && total > 0 && (
                    <span className="rounded bg-primary/15 px-1.5 py-0.5 text-xs font-semibold text-primary">
                      {((tooltip.value / total) * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                {tooltip.value > 0 && maxValue > 0 && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${(tooltip.value / maxValue) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {Math.round((tooltip.value / maxValue) * 100)}% do pico
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
