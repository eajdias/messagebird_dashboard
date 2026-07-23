"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  MessageSquare,
  Users,
  Clock,
  MessagesSquare,
  TrendingUp,
  Building2,
  AlertCircle,
  RefreshCw,
  UserCircle2,
} from "lucide-react";
import api from "@/lib/api";
import { useDashboard } from "@/hooks/useDashboard";
import { useExecutive, granularityWindow } from "@/hooks/useExecutive";
import type { EvolutionGranularity, AgentItem } from "@/types";
import { KPICard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { SegmentedToggle } from "@/components/ui/segmented-toggle";
import { Tabs, readTabFromQuery, type TabOption } from "@/components/ui/tabs";
import { AgentMultiSelect } from "@/components/dashboard/agent-multi-select";
import { DepartmentMultiSelect } from "@/components/dashboard/department-multi-select";
import { DepartmentAgents } from "@/components/dashboard/department-agents";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DashboardTab = "overview" | "executive" | "bsc";

const TAB_OPTIONS: TabOption<DashboardTab>[] = [
  { value: "overview", label: "Visão Geral" },
  { value: "executive", label: "Executivo" },
  { value: "bsc", label: "BSC" },
];

const GRANULARITY_OPTIONS: { value: EvolutionGranularity; label: string }[] = [
  { value: "day", label: "Diário" },
  { value: "week", label: "Semanal" },
  { value: "month", label: "Mensal" },
];

const DOW_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

// ── Dynamic imports ────────────────────────────────────────────────────────

const EvolutionChart = dynamic(
  () => import("@/components/dashboard/evolution-chart").then((m) => ({ default: m.EvolutionChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const AgentRanking = dynamic(
  () => import("@/components/dashboard/agent-ranking").then((m) => ({ default: m.AgentRanking })),
  { loading: () => <TableSkeleton rows={5} /> }
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

const AgentComparison = dynamic(
  () => import("@/components/dashboard/agent-comparison").then((m) => ({ default: m.AgentComparison })),
  { loading: () => <ChartSkeleton /> }
);

const HourlyChart = dynamic(
  () => import("@/components/dashboard/hourly-chart").then((m) => ({ default: m.HourlyChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const QualityOverview = dynamic(
  () => import("@/components/dashboard/quality-overview").then((m) => ({ default: m.QualityOverview })),
  { loading: () => <ChartSkeleton /> }
);

const NPSCard = dynamic(
  () => import("@/components/dashboard/nps-card").then((m) => ({ default: m.NPSCard })),
  { loading: () => <ChartSkeleton /> }
);

const NotasCard = dynamic(
  () => import("@/components/dashboard/notas-card").then((m) => ({ default: m.NotasCard })),
  { loading: () => <ChartSkeleton /> }
);

const DemandBars = dynamic(
  () => import("@/components/dashboard/demand-bars").then((m) => ({ default: m.DemandBars })),
  { loading: () => <ChartSkeleton /> }
);

const DepartmentChartComp = dynamic(
  () => import("@/components/dashboard/department-chart").then((m) => ({ default: m.DepartmentChart })),
  { loading: () => <ChartSkeleton /> }
);

const BSCExecutiveTable = dynamic(
  () => import("@/components/dashboard/bsc-executive-table").then((m) => ({ default: m.BSCExecutiveTable })),
  { loading: () => <TableSkeleton rows={6} /> }
);

// ── Skeletons ──────────────────────────────────────────────────────────────

function KPIGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} variant="glass">
          <CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader>
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
      <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
      <CardContent><Skeleton className="h-[300px] w-full" /></CardContent>
    </Card>
  );
}

function TableSkeleton({ rows }: { rows: number }) {
  return (
    <Card variant="glass">
      <CardHeader><Skeleton className="h-5 w-40" /></CardHeader>
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

function PageLoader() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-36" />
      <KPIGridSkeleton />
    </div>
  );
}

// ── Inner component (uses useSearchParams, requires Suspense) ───────────────

function DashboardContent({ mounted }: { mounted: boolean }) {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [tab, setTabState] = useState<DashboardTab>(
    () => readTabFromQuery(searchParams, "tab", TAB_OPTIONS, "overview")
  );
  const [granularity, setGranularity] = useState<EvolutionGranularity>("month");
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [agentList, setAgentList] = useState<AgentItem[]>([]);

  const setTab = useCallback(
    (next: DashboardTab) => {
      if (next === tab) return;
      setTabState(next);
      const params = new URLSearchParams(searchParams.toString());
      params.set("tab", next);
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [tab, searchParams, router]
  );

  // Fetch agent list for the multi-select
  useEffect(() => {
    api
      .get<{ agents: AgentItem[] }>("/api/v1/admin/agents?include_db=true")
      .then((r) => setAgentList(r.data.agents))
      .catch(() => {});
  }, []);

  // Dashboard data (always loaded for overview tab KPIs)
  const { summary, agents, channels, granularEvolution, loading, error } = useDashboard({ granularity });

  // Executive data (lazy — only for executive/bsc tabs)
  const execWindow = granularityWindow(granularity);
  const executive = useExecutive({
    startDate: execWindow.startDate,
    endDate: execWindow.endDate,
    granularity,
    selectedDept: selectedDept || undefined,
    group: "Suporte Tecnico",
  });

  if (!mounted || loading) {
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

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Tabs value={tab} onChange={setTab} options={TAB_OPTIONS} paramName="tab" />
      </div>
      <div className="flex items-center gap-3">
        {tab !== "overview" && tab !== "bsc" && (
          <DepartmentMultiSelect
            selected={selectedDept ? [selectedDept] : []}
            onChange={(v) => setSelectedDept(v.length > 0 ? v[0] : "")}
          />
        )}
        <SegmentedToggle value={granularity} onChange={setGranularity} options={GRANULARITY_OPTIONS} />
      </div>
    </div>
  );

  if (tab === "overview") {
    return (
      <div className="space-y-6">
        {header}

        <div className="bento-grid sm:grid-cols-2 sm:gap-4 lg:gap-4">
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
            subtitle={`${summary?.unique_contacts ?? 0} clientes${summary?.returning_contacts ? ` · ${summary.returning_contacts} retornantes` : ""}`}
            className="bento-conv"
            sparklineData={granularEvolution?.buckets?.map((e) => ({ value: e.total_conversations }))}
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
            sparklineData={granularEvolution?.buckets?.map((e) => ({ value: e.art_avg_minutes ?? 0 }))}
            sparklineColor="var(--chart-3)"
            icon={Clock}
            accentColor="warning"
            index={2}
          />
          <KPICard
            title="Mensagens"
            value={summary?.total_messages ?? 0}
            className="bento-msg"
            sparklineData={granularEvolution?.buckets?.map((e) => ({ value: e.total_conversations }))}
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
              <EvolutionChart data={granularEvolution?.buckets ?? []} />
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
              <AgentComparison agents={agents?.agents ?? []} />
            </Suspense>
          </motion.div>

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
        </div>
      </div>
    );
  }

  if (tab === "executive") {
    const execLoading = executive.loading;
    // DOW items with peak hour info (derived from heatmap data)
    const heatmapData = executive.heatmap;
    const dowPeaks = new Map<string, { hour: number; value: number }>();
    if (heatmapData?.cells) {
      for (const c of heatmapData.cells) {
        const dayLabel = DOW_NAMES[c.day] ?? `Dia ${c.day}`;
        const prev = dowPeaks.get(dayLabel);
        if (!prev || c.value > prev.value) {
          dowPeaks.set(dayLabel, { hour: c.hour, value: c.value });
        }
      }
    }
    const dowData = executive.dow;
    const dowItems = (dowData?.items ?? [])
      .filter((m) => m.label !== "Domingo")
      .map((m) => {
        const peak = dowPeaks.get(m.label);
        return {
          label: m.label,
          value: m.value,
          pct: m.pct,
          peakHour: peak ? `${peak.hour}h · ${peak.value} chats` : null,
        };
      });
    const dowMax = Math.max(...dowItems.map((d) => d.value), 1);
    const dowTotal = dowData?.total ?? 0;

    return (
      <div className="space-y-6">
        {header}
        {execLoading ? (
          <div className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2"><ChartSkeleton /><ChartSkeleton /></div>
            <ChartSkeleton />
            <div className="grid gap-4 lg:grid-cols-2"><ChartSkeleton /><ChartSkeleton /></div>
            <ChartSkeleton />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <UserCircle2 className="h-4 w-4" />
              <span>
                {selectedDept
                  ? selectedDept
                  : "Todos os departamentos"}{" "}
                · {executive.meta?.total_chats ?? 0} chats no período
              </span>
              <span className="ml-auto">
                {execWindow.startDate} → {execWindow.endDate}
              </span>
            </div>
            <DepartmentAgents
              department={selectedDept}
              agents={agentList}
              activeNames={executive.agents?.items?.map((a) => a.name)}
            />
            <div className="grid gap-4 lg:grid-cols-2">
              <Suspense fallback={<ChartSkeleton />}>
                <HourlyChart heatmap={executive.heatmap} />
              </Suspense>
              <Card variant="glass">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Por Dia da Semana</CardTitle>
                    <span className="text-xs text-muted-foreground">Total: {dowTotal}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  {dowItems.length === 0 ? (
                    <p className="text-xs text-muted-foreground">Sem dados no período</p>
                  ) : (
                    <div className="space-y-1.5">
                      {dowItems.map((d, i) => (
                        <div key={i} className="space-y-0.5" title={d.peakHour ? `Pico: ${d.peakHour}` : ""}>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">{d.label}</span>
                            <span className="font-medium tabular-nums">
                              {d.value}{" "}
                              <span className="text-muted-foreground">({d.pct.toFixed(0)}%)</span>
                            </span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-white/5">
                            <div
                              className="h-full rounded-full bg-chart-3 transition-all"
                              style={{ width: `${(d.value / dowMax) * 100}%` }}
                            />
                          </div>
                          {d.peakHour && (
                            <p className="text-[10px] text-muted-foreground/60">Pico: {d.peakHour}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <Suspense fallback={<ChartSkeleton />}>
                <NPSCard breakdown={executive.quality?.nps_breakdown ?? null} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <NotasCard rating={executive.quality?.rating ?? null} />
              </Suspense>
            </div>
            <Suspense fallback={<ChartSkeleton />}>
              <DemandBars
                motives={executive.motives}
                occurrences={executive.occurrences}
                dow={executive.dow}
                hideDOW
              />
            </Suspense>
            <Suspense fallback={<ChartSkeleton />}>
              <DepartmentChartComp data={executive.departments} />
            </Suspense>
          </>
        )}
      </div>
    );
  }

  // tab === "bsc"
  return (
    <div className="space-y-6">
      {header}
      <Suspense fallback={<TableSkeleton rows={6} />}>
        <BSCExecutiveTable data={executive.bsc} />
      </Suspense>
    </div>
  );
}

// ── Outer page component (Suspense wrapper for useSearchParams) ─────────────

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <Suspense fallback={<PageLoader />}>
      <DashboardContent mounted={mounted} />
    </Suspense>
  );
}
