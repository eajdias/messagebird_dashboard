"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentRow } from "@/types";

interface AgentContributionProps {
  agents: AgentRow[];
  className?: string;
}

const METRICS = [
  { key: "chats" as const, label: "Chats" },
  { key: "promoters" as const, label: "Promotores" },
  { key: "detractors" as const, label: "Detratores" },
  { key: "highNotes" as const, label: "Notas Altas" },
  { key: "lowNotes" as const, label: "Notas Baixas" },
  { key: "neutralNotes" as const, label: "Neutros" },
  { key: "goodArt" as const, label: "ART ≤10" },
  { key: "acceptableArt" as const, label: "ART 10-30" },
  { key: "badArt" as const, label: "ART >30" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

function pct(part: number, total: number): number {
  return total > 0 ? Math.round((part / total) * 100) : 0;
}

export const AgentContribution = memo(function AgentContribution({ agents, className }: AgentContributionProps) {
  const rows = useMemo(() => {
    const totals: Record<MetricKey, number> = {
      chats: agents.reduce((s, a) => s + a.chats, 0),
      promoters: agents.reduce((s, a) => s + (a.nps_score_distribution["9"] ?? 0) + (a.nps_score_distribution["10"] ?? 0), 0),
      detractors: agents.reduce((s, a) => {
        let sum = 0;
        for (let i = 1; i <= 6; i++) sum += a.nps_score_distribution[String(i)] ?? 0;
        return s + sum;
      }, 0),
      highNotes: agents.reduce((s, a) => s + a.compliments, 0),
      lowNotes: agents.reduce((s, a) => s + a.negatives, 0),
      neutralNotes: agents.reduce((s, a) => s + (a.rating_distribution["3"] ?? 0), 0),
      goodArt: agents.reduce((s, a) => s + (a.good_art_chats ?? 0), 0),
      acceptableArt: agents.reduce((s, a) => s + (a.acceptable_art_chats ?? 0), 0),
      badArt: agents.reduce((s, a) => s + (a.bad_art_chats ?? 0), 0),
    };

    const sorted = [...agents].sort((a, b) => b.chats - a.chats);

    return sorted.map((a) => ({
      name: a.name,
      chats: pct(a.chats, totals.chats),
      promoters: pct(
        (a.nps_score_distribution["9"] ?? 0) + (a.nps_score_distribution["10"] ?? 0),
        totals.promoters,
      ),
      detractors: pct(
        [1, 2, 3, 4, 5, 6].reduce((s, i) => s + (a.nps_score_distribution[String(i)] ?? 0), 0),
        totals.detractors,
      ),
      highNotes: pct(a.compliments, totals.highNotes),
      lowNotes: pct(a.negatives, totals.lowNotes),
      neutralNotes: pct(a.rating_distribution["3"] ?? 0, totals.neutralNotes),
      goodArt: pct(a.good_art_chats ?? 0, totals.goodArt),
      acceptableArt: pct(a.acceptable_art_chats ?? 0, totals.acceptableArt),
      badArt: pct(a.bad_art_chats ?? 0, totals.badArt),
    }));
  }, [agents]);

  if (rows.length === 0) {
    return (
      <Card variant="glass" className={className}>
        <CardHeader><CardTitle className="text-sm font-medium">Contribuição por Agente</CardTitle></CardHeader>
        <CardContent><p className="text-xs text-muted-foreground">Sem dados de agentes no período</p></CardContent>
      </Card>
    );
  }

  return (
    <Card variant="glass" className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Contribuição por Agente (%)</CardTitle>
          <span className="text-xs text-muted-foreground">{rows.length} agente{rows.length > 1 ? "s" : ""}</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-1.5 text-left font-medium text-muted-foreground sticky left-0 bg-card z-10">Agente</th>
                {METRICS.map((m) => (
                  <th key={m.key} className="px-2 py-1.5 text-right font-medium text-muted-foreground whitespace-nowrap">{m.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <motion.tr
                  key={r.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="border-b border-white/5 hover:bg-white/[0.03]"
                >
                  <td className="max-w-[140px] truncate py-1.5 sticky left-0 bg-card z-10">{r.name}</td>
                  {METRICS.map((m) => (
                    <td key={m.key} className="px-2 py-1.5 text-right tabular-nums">
                      <span className={r[m.key] >= 50 ? "font-bold text-chart-2" : r[m.key] === 0 ? "text-muted-foreground" : ""}>
                        {r[m.key]}%
                      </span>
                    </td>
                  ))}
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
});