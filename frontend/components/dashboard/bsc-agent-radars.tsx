"use client";

import { useCallback, useMemo } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, Tooltip,
} from "recharts";
import { useTheme } from "next-themes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BSCScorecardCategory, BSCMetricRow } from "@/types";

const AGENT_COLORS = [
  "hsl(142 76% 43%)",   // emerald
  "hsl(217 91% 60%)",   // blue
  "hsl(24 95% 53%)",    // orange
  "hsl(271 81% 58%)",   // violet
];

interface Props {
  agents: string[];
  categories: BSCScorecardCategory[];
  penalidades: BSCMetricRow[];
}

interface RadarPoint {
  category: string;
  pct: number;
  raw: number;
  rawLabel: string;
  reference: number;
}

function TooltipContent({ active, payload, color, dark }: {
  active?: boolean;
  payload?: { payload: RadarPoint }[];
  color: string;
  dark: boolean;
}) {
  if (!active || !payload?.length) return null;
  const pt = payload[0]?.payload;
  if (!pt) return null;
  const bg = dark ? "hsl(215 28% 17%)" : "hsl(0 0% 100%)";
  const fg = dark ? "hsl(210 40% 98%)" : "hsl(222 47% 11%)";
  const mute = dark ? "hsl(215 16% 61%)" : "hsl(215 16% 47%)";

  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-lg"
      style={{ background: bg, color: fg, borderColor: dark ? "hsl(217 33% 18%)" : "hsl(214 32% 91%)" }}
    >
      <p className="font-semibold" style={{ fontSize: 13 }}>{pt.category}</p>
      <p style={{ color: mute }}>{pt.rawLabel}</p>
      <p className="font-bold" style={{ color }}>{pt.pct}%</p>
    </div>
  );
}

export function BSCAgentRadars({ agents, categories, penalidades }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  // Compute max per category for normalization
  const maxPerCategory = useMemo(() => {
    const maxVals: number[] = [];
    for (const cat of categories) {
      let catMax = 0;
      for (const m of cat.metrics) {
        catMax += m.per_agent.reduce((best, a) => Math.max(best, a.kpi_score ?? 0), 0);
      }
      maxVals.push(catMax || 1);
    }
    if (penalidades.length > 0) {
      let pMax = 0;
      for (const p of penalidades) {
        pMax += p.per_agent.reduce((best, a) => Math.max(best, a.kpi_score ?? 0), 0);
      }
      maxVals.push(pMax || 1);
    }
    return maxVals;
  }, [categories, penalidades]);

  // Theme-aware style tokens
  const theme = useMemo(() => ({
    gridStroke: dark ? "hsl(217 33% 25%)" : "hsl(214 32% 85%)",
    gridFill: dark ? "hsl(222 47% 11% / 0.25)" : "hsl(210 20% 98% / 0.6)",
    tickFill: dark ? "hsl(210 40% 90%)" : "hsl(215 28% 30%)",
    referenceStroke: dark ? "hsl(215 16% 50% / 0.5)" : "hsl(215 16% 60% / 0.5)",
    referenceFill: "none",
    chartBg: dark ? "hsl(222 47% 11%)" : "hsl(0 0% 100%)",
    axisStroke: dark ? "hsl(217 33% 25%)" : "hsl(214 32% 85%)",
  }), [dark]);

  const agentData = useMemo(() => {
    return agents.map((agent, agentIdx) => {
      const radarData: RadarPoint[] = [];
      let catIdx = 0;
      for (const cat of categories) {
        let raw = 0;
        for (const m of cat.metrics) {
          const av = m.per_agent.find((a) => a.agent_name === agent);
          raw += av?.kpi_score ?? 0;
        }
        const shortName = cat.name.length > 14 ? cat.name.slice(0, 14) + "…" : cat.name;
        radarData.push({
          category: shortName,
          pct: maxPerCategory[catIdx] > 0 ? Math.round((raw / maxPerCategory[catIdx]) * 100) : 0,
          raw,
          rawLabel: `${raw.toFixed(1)} pts / máx ${maxPerCategory[catIdx]?.toFixed(0)}`,
          reference: 100,
        });
        catIdx++;
      }
      if (penalidades.length > 0) {
        let raw = 0;
        for (const p of penalidades) {
          const av = p.per_agent.find((a) => a.agent_name === agent);
          raw += av?.kpi_score ?? 0;
        }
        radarData.push({
          category: "Penalidades",
          pct: maxPerCategory[catIdx] > 0 ? 100 - Math.round((Math.abs(raw) / maxPerCategory[catIdx]) * 100) : 0,
          raw,
          rawLabel: `${raw.toFixed(1)} pts`,
          reference: 100,
        });
      }
      return { agent, color: AGENT_COLORS[agentIdx % AGENT_COLORS.length], data: radarData };
    });
  }, [agents, categories, penalidades, maxPerCategory]);

  const customTick = useCallback(
    (props: { payload?: { value: string }; x?: number | string; y?: number | string; textAnchor?: "start" | "middle" | "end" | "inherit" }) => {
      const { payload, x: _x = 0, y: _y = 0, textAnchor = "middle" } = props;
      if (!payload) return null;
      const x = Number(_x);
      const y = Number(_y);

      const lines = payload.value.length > 12
        ? [payload.value.slice(0, 12), payload.value.slice(12)]
        : [payload.value];

      return (
        <g>
          {lines.map((line, i) => (
            <text
              key={i}
              x={x}
              y={y + (i - (lines.length - 1) / 2) * 14}
              textAnchor={textAnchor}
              fill={theme.tickFill}
              fontSize={12}
              fontWeight={500}
            >
              {line}
            </text>
          ))}
        </g>
      );
    },
    [theme.tickFill]
  );

  const cols = Math.min(agents.length, 2);

  return (
    <div
      className="grid gap-5"
      style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
    >
      {agentData.map(({ agent, color, data }) => (
        <Card
          key={agent}
          className="overflow-hidden"
          style={{
            borderColor: color + "50",
            borderWidth: 1.5,
          }}
        >
          <CardHeader className="py-2.5 px-4 flex flex-row items-center gap-2">
            <div
              className="h-3.5 w-3.5 rounded-full shrink-0"
              style={{ backgroundColor: color }}
            />
            <CardTitle
              className="font-semibold text-sm truncate"
              title={agent}
              style={{ color: color }}
            >
              {agent.split(" ").slice(0, 2).join(" ")}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-2 pb-3">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart
                data={data}
                cx="50%"
                cy="50%"
                outerRadius="70%"
                style={{ background: theme.chartBg }}
              >
                <PolarGrid
                  gridType="circle"
                  stroke={theme.gridStroke}
                  strokeWidth={1}
                  fill={theme.gridFill}
                />
                <PolarAngleAxis
                  dataKey="category"
                  tick={customTick}
                  axisLine={{ stroke: theme.axisStroke, strokeWidth: 1 }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={false}
                  axisLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => (
                    <TooltipContent
                      active={active}
                      payload={payload as unknown as { payload: RadarPoint }[]}
                      color={color}
                      dark={dark}
                    />
                  )}
                />
                {/* Reference 100% boundary */}
                <Radar
                  dataKey="reference"
                  stroke={theme.referenceStroke}
                  fill={theme.referenceFill}
                  strokeWidth={1.5}
                  strokeDasharray="5 4"
                />
                {/* Actual data */}
                <Radar
                  name={agent.split(" ")[0]}
                  dataKey="pct"
                  stroke={color}
                  fill={color}
                  fillOpacity={dark ? 0.18 : 0.12}
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: color, strokeWidth: 0 }}
                  activeDot={{ r: 6, fill: color, strokeWidth: 0 }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
