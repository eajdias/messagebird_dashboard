"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { MessageSquare, Users, Clock, MessagesSquare, TrendingUp, Building2 } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { KPICard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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

const NPSGauge = dynamic(
  () => import("@/components/dashboard/nps-gauge").then((m) => ({ default: m.NPSGauge })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const ChannelChart = dynamic(
  () => import("@/components/dashboard/channel-chart").then((m) => ({ default: m.ChannelChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const AgentRadar = dynamic(
  () => import("@/components/dashboard/agent-radar").then((m) => ({ default: m.AgentRadar })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

function KPIGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} variant="glass">
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
    <Card variant="glass">
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
    <Card variant="glass">
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
        <EmptyState
          icon={<AlertCircle className="h-12 w-12 text-destructive" />}
          title="Erro ao carregar dashboard"
          description={error}
          action={
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="mr-1 h-4 w-4" />
              Tentar novamente
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:bento-grid">
        <motion.div
          className={cn("bento-nps")}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05, ease: "easeOut" }}
        >
          <Suspense fallback={<ChartSkeleton />}>
            <NPSGauge value={summary?.nps_score ?? null} className="h-full" />
          </Suspense>
        </motion.div>

        <KPICard
          title="Conversas"
          value={summary?.total_conversations ?? 0}
          subtitle={`${summary?.unique_contacts ?? 0} clientes únicos`}
          className="bento-conv"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.total_conversations }))}
          sparklineColor="var(--chart-2)"
          icon={MessageSquare}
          accentColor="success"
          index={1}
        />
        <KPICard
          title="ART (min)"
          value={summary?.art_avg_minutes != null ? summary.art_avg_minutes.toFixed(1) : "—"}
          subtitle={summary?.sla_compliance_pct != null ? `SLA: ${summary.sla_compliance_pct.toFixed(1)}%` : undefined}
          className="bento-art"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.art_avg_minutes ?? 0 }))}
          sparklineColor="var(--chart-3)"
          icon={Clock}
          accentColor="warning"
          index={2}
        />
        <KPICard
          title="Mensagens"
          value={summary?.total_messages ?? 0}
          subtitle={summary?.returning_contacts ? `${summary.returning_contacts} retornantes` : undefined}
          className="bento-msg"
          sparklineData={evolution?.evolution?.map((e) => ({ value: e.total_conversations }))}
          sparklineColor="var(--chart-4)"
          icon={MessagesSquare}
          accentColor="purple"
          index={3}
        />

        <motion.div
          className="bento-chart"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25, ease: "easeOut" }}
        >
          <Suspense fallback={<ChartSkeleton />}>
            <EvolutionChart data={evolution?.evolution ?? []} />
          </Suspense>
        </motion.div>

        <motion.div
          className="bento-chan"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.35, ease: "easeOut" }}
        >
          <Suspense fallback={<ChartSkeleton />}>
            <ChannelChart channels={channels?.channels ?? []} />
          </Suspense>
        </motion.div>

        <motion.div
          className="bento-agents"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.45, ease: "easeOut" }}
        >
          <Suspense fallback={<ChartSkeleton />}>
            <AgentRadar agents={agents?.agents ?? []} />
          </Suspense>
        </motion.div>

        {bsc && (bsc.data_t1.length > 0 || bsc.data_t2.length > 0) && (
          <motion.div
            className="bento-bsc"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.55, ease: "easeOut" }}
          >
            <Suspense fallback={<TableSkeleton rows={4} />}>
              <BSCTable header={bsc.header} data_t1={bsc.data_t1} data_t2={bsc.data_t2} />
            </Suspense>
          </motion.div>
        )}

        {(agents?.agents?.length ?? 0) > 0 && (
          <motion.div
            className="sm:col-span-2 lg:col-span-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.6, ease: "easeOut" }}
          >
            <Suspense fallback={<TableSkeleton rows={5} />}>
              <AgentRanking agents={agents?.agents ?? []} />
            </Suspense>
          </motion.div>
        )}

        {(channels?.channels?.length ?? 0) > 0 && (
          <motion.div
            className="sm:col-span-2 lg:col-span-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.65, ease: "easeOut" }}
          >
            <Suspense fallback={<TableSkeleton rows={3} />}>
              <ChannelBreakdown channels={channels?.channels ?? []} />
            </Suspense>
          </motion.div>
        )}
      </div>
    </div>
  );
}
