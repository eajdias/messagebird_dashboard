"use client";

import { useMemo } from "react";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { BSCScorecardCategory, BSCMetricRow } from "@/types";

interface Props {
  agents: string[];
  categories: BSCScorecardCategory[];
  penalidades: BSCMetricRow[];
}

export function BSCAgentRadars({ agents, categories, penalidades }: Props) {
  const allMetrics = useMemo(
    () => [...categories.flatMap((c) => c.metrics), ...penalidades],
    [categories, penalidades]
  );

  const categoryNames = useMemo(
    () => [...categories.map((c) => c.name), ...(penalidades.length > 0 ? ["Penalidades"] : [])],
    [categories, penalidades]
  );

  const maxPerCategory = useMemo(() => {
    const maxVals: number[] = [];
    let mi = 0;
    for (const cat of categories) {
      let catMax = 0;
      for (const m of cat.metrics) {
        catMax += m.per_agent.reduce((best, a) => Math.max(best, a.kpi_score ?? 0), 0);
      }
      maxVals.push(catMax || 1);
      mi++;
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

  const agentData = useMemo(() => {
    return agents.map((agent) => {
      const radarData: { category: string; pct: number; raw: number }[] = [];
      let catIdx = 0;
      for (const cat of categories) {
        let raw = 0;
        for (const m of cat.metrics) {
          const av = m.per_agent.find((a) => a.agent_name === agent);
          raw += av?.kpi_score ?? 0;
        }
        radarData.push({
          category: cat.name.length > 18 ? cat.name.slice(0, 18) + "..." : cat.name,
          pct: maxPerCategory[catIdx] > 0 ? Math.round((raw / maxPerCategory[catIdx]) * 100) : 0,
          raw,
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
          pct: maxPerCategory[catIdx] > 0 ? Math.round((raw / maxPerCategory[catIdx]) * 100) : 0,
          raw,
        });
        catIdx++;
      }
      return { agent, data: radarData };
    });
  }, [agents, categories, penalidades, maxPerCategory]);

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(agents.length, 4)}, 1fr)` }}>
      {agentData.map(({ agent, data }) => (
        <Card key={agent} className="overflow-hidden">
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-xs font-medium truncate" title={agent}>
              {agent.split(" ").slice(0, 2).join(" ")}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 pb-2">
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={data} cx="50%" cy="50%" outerRadius="65%">
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="category"
                  tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fontSize: 8, fill: "hsl(var(--muted-foreground))" }}
                  tickCount={4}
                />
                <Radar
                  name={agent.split(" ")[0]}
                  dataKey="pct"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
