"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useDashboard } from "@/hooks/useDashboard";
import { KPICard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

const EvolutionChart = dynamic(
  () => import("@/components/dashboard/evolution-chart").then((m) => ({ default: m.EvolutionChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const AgentRanking = dynamic(
  () => import("@/components/dashboard/agent-ranking").then((m) => ({ default: m.AgentRanking })),
  { loading: () => <TableSkeleton rows={5} /> }
);

const ChannelBreakdown = dynamic(
  () => import("@/components/dashboard/channel-breakdown").then((m) => ({ default: m.ChannelBreakdown })),
  { loading: () => <TableSkeleton rows={3} /> }
);

const BSCTable = dynamic(
  () => import("@/components/dashboard/bsc-table").then((m) => ({ default: m.BSCTable })),
  { loading: () => <TableSkeleton rows={4} /> }
);

function KPIGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-4 w-24" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="mt-2 h-3 w-32" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[300px] w-full" />
      </CardContent>
    </Card>
  );
}

function TableSkeleton({ rows }: { rows: number }) {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          {Array.from({ length: rows }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { summary, bsc, evolution, agents, channels, loading, error } = useDashboard({ months: 12 });

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <KPIGridSkeleton />
        <div className="grid gap-6 lg:grid-cols-2">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
        <TableSkeleton rows={5} />
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

      <div className="grid gap-4 sm:grid-cols-2 lg:bento-grid">
        <KPICard
          title="NPS"
          value={summary?.nps_score != null ? summary.nps_score.toFixed(1) : "—"}
          subtitle={summary?.nps_score != null ? (summary.nps_score >= 50 ? "Excelente" : summary.nps_score >= 0 ? "Neutro" : "Negativo") : undefined}
          trend={summary?.nps_score != null ? (summary.nps_score >= 50 ? "up" : summary.nps_score >= 0 ? "neutral" : "down") : undefined}
          className="bento-nps bg-gradient-to-br from-primary/5 to-primary/10 ring-1 ring-primary/20"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.nps_score ?? 0 }))}
          sparklineColor="var(--chart-1)"
        />
        <KPICard
          title="Conversas"
          value={summary?.total_conversations ?? 0}
          subtitle={`${summary?.unique_contacts ?? 0} clientes únicos`}
          className="bento-conv"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.total_conversations }))}
          sparklineColor="var(--chart-2)"
        />
        <KPICard
          title="ART (min)"
          value={summary?.art_avg_minutes != null ? summary.art_avg_minutes.toFixed(1) : "—"}
          subtitle={summary?.sla_compliance_pct != null ? `SLA: ${summary.sla_compliance_pct.toFixed(1)}%` : undefined}
          className="bento-art"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.art_avg_minutes ?? 0 }))}
          sparklineColor="var(--chart-3)"
        />
        <KPICard
          title="Mensagens"
          value={summary?.total_messages ?? 0}
          subtitle={summary?.returning_contacts ? `${summary.returning_contacts} retornantes` : undefined}
          className="bento-msg"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.total_conversations }))}
          sparklineColor="var(--chart-4)"
        />
        <motion.div
          className="bento-chart"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15, ease: "easeOut" }}
        >
          <Suspense fallback={<ChartSkeleton />}>
            <EvolutionChart data={evolution?.evolution ?? []} />
          </Suspense>
        </motion.div>
        <motion.div
          className="bento-chan"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25, ease: "easeOut" }}
        >
          <Suspense fallback={<TableSkeleton rows={3} />}>
            <ChannelBreakdown channels={channels?.channels ?? []} />
          </Suspense>
        </motion.div>
        <motion.div
          className="bento-agents"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.35, ease: "easeOut" }}
        >
          <Suspense fallback={<TableSkeleton rows={5} />}>
            <AgentRanking agents={agents?.agents ?? []} />
          </Suspense>
        </motion.div>
        {bsc && (bsc.data_t1.length > 0 || bsc.data_t2.length > 0) && (
          <motion.div
            className="bento-bsc"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.45, ease: "easeOut" }}
          >
            <Suspense fallback={<TableSkeleton rows={4} />}>
              <BSCTable header={bsc.header} data_t1={bsc.data_t1} data_t2={bsc.data_t2} />
            </Suspense>
          </motion.div>
        )}
      </div>
    </div>
  );
}
