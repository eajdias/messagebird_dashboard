"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AgentRow } from "@/types";

interface AgentContributionProps {
  agents: AgentRow[];
  className?: string;
}

const METRICS = [
  { key: "chats" as const, label: "Chats", pctOf: "chats" as const },
  { key: "promoters" as const, label: "Promotores", pctOf: "promoters" as const },
  { key: "detractors" as const, label: "Detratores", pctOf: "detractors" as const },
  { key: "highNotes" as const, label: "Notas Altas", pctOf: "highNotes" as const },
  { key: "lowNotes" as const, label: "Notas Baixas", pctOf: "lowNotes" as const },
  { key: "goodArt" as const, label: "ART Bom", pctOf: "goodArt" as const },
  { key: "badArt" as const, label: "ART Ruim", pctOf: "badArt" as const },
] as const;

function pct(part: number, total: number): number {
  return total > 0 ? Math.round((part / total) * 100) : 0;
}

export function AgentContribution({ agents, className }: AgentContributionProps) {
  const rows = useMemo(() => {
    const totals = {
      chats: agents.reduce((s, a) => s + a.chats, 0),
      promoters: agents.reduce((s, a) => s + (a.nps_score_distribution["9"] ?? 0) + (a.nps_score_distribution["10"] ?? 0), 0),
      detractors: agents.reduce((s, a) => {
        let sum = 0;
        for (let i = 1; i <= 6; i++) sum += a.nps_score_distribution[String(i)] ?? 0;
        return s + sum;
      }, 0),
      highNotes: agents.reduce((s, a) => s + a.compliments, 0),
      lowNotes: agents.reduce((s, a) => s + a.negatives, 0),
      goodArt: agents.reduce((s, a) => s + (a.good_art_chats ?? 0), 0),
      badArt: agents.reduce((s, a) => s + (a.bad_art_chats ?? 0), 0),
    };

    const top = [...agents]
      .sort((a, b) => b.chats - a.chats)
      .slice(0, 10);

    return top.map((a) => ({
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
      goodArt: pct(a.good_art_chats, totals.goodArt),
      badArt: pct(a.bad_art_chats, totals.badArt),
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
        <CardTitle className="text-sm font-medium">Contribuição por Agente (%)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-1.5 text-left font-medium text-muted-foreground">Agente</th>
                {METRICS.map((m) => (
                  <th key={m.key} className="px-2 py-1.5 text-right font-medium text-muted-foreground">{m.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <motion.tr
                  key={r.name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-white/5 hover:bg-white/[0.03]"
                >
                  <td className="max-w-[140px] truncate py-1.5">{r.name}</td>
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
}
