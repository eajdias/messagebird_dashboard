"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, safeNum } from "@/lib/utils";
import type { NPSBreakdown, QualityDistribution } from "@/types";

interface QualityOverviewProps {
  rating: QualityDistribution | null;
  npsScore: QualityDistribution | null;
  npsBreakdown: NPSBreakdown | null;
  className?: string;
}

const RATING_COLORS = [
  "var(--destructive)",
  "var(--destructive)",
  "var(--chart-3)",
  "var(--chart-2)",
  "var(--chart-2)",
];

const NPS_COLORS = Array.from({ length: 10 }, (_, i) => {
  const v = i + 1;
  if (v >= 9) return "var(--chart-2)";
  if (v >= 7) return "var(--chart-3)";
  return "var(--destructive)";
});

const NPS_BREAKDOWN_COLORS = {
  promoters: "var(--chart-2)",
  neutrals: "var(--chart-3)",
  detractors: "var(--destructive)",
};

function formatValue(v: unknown): string {
  return safeNum(v).toFixed(1);
}

function buildRatingData(rating: QualityDistribution | null) {
  return [1, 2, 3, 4, 5].map((n) => ({
    label: `Nota ${n}`,
    value: safeNum(rating?.counts?.[String(n)] ?? 0),
    color: RATING_COLORS[n - 1],
  }));
}

function buildNpsData(nps: QualityDistribution | null) {
  return Array.from({ length: 10 }, (_, i) => {
    const n = i + 1;
    return {
      label: String(n),
      value: safeNum(nps?.counts?.[String(n)] ?? 0),
      color: NPS_COLORS[i],
    };
  });
}

function buildNpsBreakdown(breakdown: NPSBreakdown | null) {
  if (!breakdown) return [];
  return [
    { key: "promoters", label: "Promotores (9-10)", value: breakdown.promoters, color: NPS_BREAKDOWN_COLORS.promoters },
    { key: "neutrals", label: "Neutros (7-8)", value: breakdown.neutrals, color: NPS_BREAKDOWN_COLORS.neutrals },
    { key: "detractors", label: "Detratores (1-6)", value: breakdown.detractors, color: NPS_BREAKDOWN_COLORS.detractors },
  ];
}

function BarTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; payload: { label: string } }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-tooltip rounded-md px-2.5 py-1.5 text-xs">
      <p className="font-semibold">{label ?? payload[0]?.payload?.label}</p>
      <p className="text-muted-foreground">{payload[0]?.value ?? 0}</p>
    </div>
  );
}

export function QualityOverview({ rating, npsScore, npsBreakdown, className }: QualityOverviewProps) {
  const ratingData = buildRatingData(rating);
  const npsData = buildNpsData(npsScore);
  const npsBdData = buildNpsBreakdown(npsBreakdown);

  const ratingMax = Math.max(...ratingData.map((d) => d.value), 1);
  const npsMax = Math.max(...npsData.map((d) => d.value), 1);
  const breakdownMax = Math.max(...npsBdData.map((d) => d.value), 1);

  const ratingTotal = rating?.total ?? 0;
  const npsTotal = npsScore?.total ?? 0;

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <CardTitle className="text-base">Qualidade & Satisfação</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <section>
          <header className="mb-2 flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              NPS Real (Promotores / Neutros / Detratores)
            </h4>
            {npsBreakdown?.real_nps != null && Number.isFinite(npsBreakdown.real_nps) && (
              <span className="text-2xl font-bold tabular-nums">
                {formatValue(npsBreakdown.real_nps)}
              </span>
            )}
          </header>
          {npsBdData.length > 0 && breakdownMax > 0 ? (
            <div className="space-y-1.5">
              {npsBdData.map((d) => (
                <div key={d.key} className="space-y-0.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{d.label}</span>
                    <span className="font-medium tabular-nums">
                      {d.value}{" "}
                      <span className="text-muted-foreground">
                        ({npsTotal > 0 ? ((d.value / npsTotal) * 100).toFixed(0) : 0}%)
                      </span>
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(d.value / breakdownMax) * 100}%`,
                        background: d.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">Sem avaliações NPS no período</p>
          )}
        </section>

        <section>
          <header className="mb-2 flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Distribuição de Notas (1-5)
            </h4>
            <span className="text-xs text-muted-foreground">Total: {ratingTotal}</span>
          </header>
          {ratingMax > 0 ? (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ratingData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <XAxis dataKey="label" tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip content={<BarTooltip />} cursor={false} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                    {ratingData.map((d, i) => (
                      <Cell key={i} fill={d.color} />
                    ))}
                    <LabelList dataKey="value" position="top" fill="var(--foreground)" fontSize={10} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">Sem notas no período</p>
          )}
        </section>

        <section>
          <header className="mb-2 flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Distribuição NPS (1-10)
            </h4>
            <span className="text-xs text-muted-foreground">Total: {npsTotal}</span>
          </header>
          {npsMax > 0 ? (
            <div className="h-28">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={npsData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <XAxis
                    dataKey="label"
                    tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis hide />
                  <Tooltip content={<BarTooltip />} cursor={false} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                    {npsData.map((d, i) => (
                      <Cell key={i} fill={d.color} />
                    ))}
                    <LabelList dataKey="value" position="top" fill="var(--foreground)" fontSize={10} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">Sem NPS no período</p>
          )}
        </section>
      </CardContent>
    </Card>
  );
}
