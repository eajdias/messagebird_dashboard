"use client";

import { useDashboard } from "@/hooks/useDashboard";
import { KPICard } from "@/components/dashboard/kpi-card";
import { EvolutionChart } from "@/components/dashboard/evolution-chart";
import { AgentRanking } from "@/components/dashboard/agent-ranking";
import { ChannelBreakdown } from "@/components/dashboard/channel-breakdown";
import { BSCTable } from "@/components/dashboard/bsc-table";

export default function DashboardPage() {
  const { summary, bsc, evolution, agents, channels, loading, error } = useDashboard({ months: 12 });

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Conversas"
          value={summary?.total_conversations ?? 0}
          subtitle={`${summary?.unique_contacts ?? 0} clientes únicos`}
        />
        <KPICard
          title="NPS"
          value={summary?.nps_score != null ? summary.nps_score.toFixed(1) : "—"}
          subtitle={summary?.nps_score != null ? (summary.nps_score >= 50 ? "Positivo" : summary.nps_score >= 0 ? "Neutro" : "Negativo") : undefined}
          trend={summary?.nps_score != null ? (summary.nps_score >= 50 ? "up" : summary.nps_score >= 0 ? "neutral" : "down") : undefined}
        />
        <KPICard
          title="ART (min)"
          value={summary?.art_avg_minutes != null ? summary.art_avg_minutes.toFixed(1) : "—"}
          subtitle={summary?.sla_compliance_pct != null ? `SLA: ${summary.sla_compliance_pct.toFixed(1)}%` : undefined}
        />
        <KPICard
          title="Mensagens"
          value={summary?.total_messages ?? 0}
          subtitle={summary?.returning_contacts ? `${summary.returning_contacts} retornantes` : undefined}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <EvolutionChart data={evolution?.evolution ?? []} />
        <ChannelBreakdown channels={channels?.channels ?? []} />
      </div>

      <AgentRanking agents={agents?.agents ?? []} />

      {bsc && (bsc.data_t1.length > 0 || bsc.data_t2.length > 0) && (
        <BSCTable header={bsc.header} data_t1={bsc.data_t1} data_t2={bsc.data_t2} />
      )}
    </div>
  );
}
