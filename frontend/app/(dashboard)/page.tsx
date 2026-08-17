"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
} from "lucide-react";
import api from "@/lib/api";
import { defaultPeriod, selectGranularity } from "@/lib/utils";
import { useDashboard } from "@/hooks/useDashboard";
import { useExecutive } from "@/hooks/useExecutive";
import { useBscScorecard } from "@/hooks/useBscScorecard";
import type { AgentItem } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { Tabs, readTabFromQuery, type TabOption } from "@/components/ui/tabs";
import { DepartmentMultiSelect } from "@/components/dashboard/department-multi-select";
import { DepartmentAgents } from "@/components/dashboard/department-agents";
import { DowChart } from "@/components/dashboard/dow-chart";
import { Button } from "@/components/ui/button";

type DashboardTab = "overview" | "executive" | "heatmap" | "bsc";

const TAB_OPTIONS: TabOption<DashboardTab>[] = [
  { value: "overview", label: "Visão Geral" },
  { value: "executive", label: "Executivo" },
  { value: "heatmap", label: "Mapa Geral" },
  { value: "bsc", label: "BSC" },
];



const DOW_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

// ── Dynamic imports ────────────────────────────────────────────────────────

const HourlyChart = dynamic(
  () => import("@/components/dashboard/heatmap-grid").then((m) => ({ default: m.HeatmapGrid })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const HourlyBarChart = dynamic(
  () => import("@/components/dashboard/hourly-bar-chart").then((m) => ({ default: m.HourlyBarChart })),
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

const BSCExecutiveTable = dynamic(
  () => import("@/components/dashboard/bsc-executive-table").then((m) => ({ default: m.BSCExecutiveTable })),
  { loading: () => <TableSkeleton rows={6} /> }
);

const ARTDistribution = dynamic(
  () => import("@/components/dashboard/art-distribution").then((m) => ({ default: m.ARTDistribution })),
  { loading: () => <ChartSkeleton /> }
);

const ReturnersCard = dynamic(
  () => import("@/components/dashboard/returners-card").then((m) => ({ default: m.ReturnersCard })),
  { loading: () => <ChartSkeleton /> }
);

const RatingEvolutionChart = dynamic(
  () => import("@/components/dashboard/rating-evolution-chart").then((m) => ({ default: m.RatingEvolutionChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const NPSEvolutionChart = dynamic(
  () => import("@/components/dashboard/nps-evolution-chart").then((m) => ({ default: m.NPSEvolutionChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const RatedBreakdownChart = dynamic(
  () => import("@/components/dashboard/rated-breakdown-chart").then((m) => ({ default: m.RatedBreakdownChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const ARTEvolutionChart = dynamic(
  () => import("@/components/dashboard/art-evolution-chart").then((m) => ({ default: m.ARTEvolutionChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const AgentContribution = dynamic(
  () => import("@/components/dashboard/agent-contribution").then((m) => ({ default: m.AgentContribution })),
  { loading: () => <ChartSkeleton /> }
);

const BSCScorecardTable = dynamic(
  () => import("@/components/dashboard/bsc-scorecard-table").then((m) => ({ default: m.BSCScorecardTable })),
  { loading: () => <TableSkeleton rows={8} /> }
);

// ── Skeletons ──────────────────────────────────────────────────────────────

function ChartSkeleton() {
  return (
    <Card variant="glass">
      <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
      <CardContent><Skeleton className="h-[200px] sm:h-[260px] lg:h-[300px] w-full" /></CardContent>
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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} variant="glass">
            <CardHeader className="pb-2"><Skeleton className="h-4 w-24" /></CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Simple stat card with loading state ────────────────────────────────────

function StatCard({ title, value, loading }: { title: string; value?: string | number; loading?: boolean }) {
  return (
    <Card variant="glass">
      <CardHeader className="pb-1"><CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle></CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-20" />
        ) : (
          <span className="text-2xl font-bold tabular-nums">{value ?? "—"}</span>
        )}
      </CardContent>
    </Card>
  );
}

// ── Inner component (uses useSearchParams, requires Suspense) ───────────────

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [tab, setTabState] = useState<DashboardTab>(
    () => readTabFromQuery(searchParams, "tab", TAB_OPTIONS, "overview")
  );
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [agentList, setAgentList] = useState<AgentItem[]>([]);

  const { start: defaultStart, end: defaultEnd } = useMemo(() => defaultPeriod(), []);

  const [pendingStart, setPendingStart] = useState<string>(defaultStart);
  const [pendingEnd, setPendingEnd] = useState<string>(defaultEnd);
  const [appliedStart, setAppliedStart] = useState<string>(defaultStart);
  const [appliedEnd, setAppliedEnd] = useState<string>(defaultEnd);

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

  useEffect(() => {
    api
      .get<{ agents: AgentItem[] }>("/api/v1/admin/agents?include_db=true")
      .then((r) => setAgentList(r.data.agents))
      .catch(() => {});
  }, []);

  const overviewActive = tab === "overview";
  const executiveActive = tab === "executive";
  const heatmapActive = tab === "heatmap";

  const granularity = useMemo(() => selectGranularity(appliedStart, appliedEnd), [appliedStart, appliedEnd]);

  const { granularEvolution, granularLoading } = useDashboard({
    granularity,
    start_date: appliedStart,
    end_date: appliedEnd,
    department: selectedDept || undefined,
    enabled: overviewActive,
  });

  const executive = useExecutive({
    startDate: appliedStart,
    endDate: appliedEnd,
    selectedDept: selectedDept || undefined,
    group: "Suporte Tecnico",
    view: executiveActive || heatmapActive ? "executive" : "overview",
    enabled: overviewActive || executiveActive || heatmapActive,
  });

  const bscScorecard = useBscScorecard({
    department: selectedDept || "",
    startDate: appliedStart,
    endDate: appliedEnd,
    enabled: tab === "bsc",
  });

  const dowMemo = useMemo(() => {
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
    const items = (dowData?.items ?? [])
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
    return {
      dowItems: items,
      dowMax: Math.max(...items.map((d) => d.value), 1),
      dowTotal: dowData?.total ?? 0,
    };
  }, [executive.heatmap, executive.dow]);

  const { dowItems, dowMax, dowTotal } = dowMemo;

  // KPI data — derived from whatever has loaded so far
  const nps = executive.quality?.nps_breakdown?.real_nps;
  const pctReturning = executive.returners?.pct_returning;

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Tabs value={tab} onChange={setTab} options={TAB_OPTIONS} paramName="tab" />
      </div>
      <div className="flex items-center gap-3">
        <DepartmentMultiSelect
          selected={selectedDept ? [selectedDept] : []}
          onChange={(v) => setSelectedDept(v.length > 0 ? v[0] : "")}
        />
        <div suppressHydrationWarning>
          <DateRangePicker
            startDate={pendingStart}
            endDate={pendingEnd}
            onChange={(s, e) => { setPendingStart(s); setPendingEnd(e); }}
            onConfirm={(s, e) => { setAppliedStart(s); setAppliedEnd(e); setPendingStart(s); setPendingEnd(e); }}
          />
        </div>
      </div>
    </div>
  );

  // ── Overview tab ────────────────────────────────────────────────────────
  if (tab === "overview") {
    return (
      <div className="space-y-4">
        {header}

        {/* KPIs */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Chats" value={executive.meta?.total_chats?.toLocaleString("pt-BR")} loading={executive.loading && !executive.meta} />
          <StatCard title="ART ≤ 10min" value={executive.meta?.pct_art_10min != null ? `${executive.meta.pct_art_10min}%` : undefined} loading={executive.loading && !executive.meta} />
          <StatCard title="NPS" value={nps != null && Number.isFinite(nps) ? nps.toFixed(1) : undefined} loading={executive.loading && !executive.quality} />
          <StatCard title="Retornantes" value={pctReturning != null ? `${pctReturning.toFixed(1)}%` : undefined} loading={executive.loading && !executive.returners} />
        </div>

        {/* 4 charts in 2x2 grid */}
        <div className="grid gap-3 lg:grid-cols-2">
          {granularLoading && !granularEvolution ? (
            <><ChartSkeleton /><ChartSkeleton /><ChartSkeleton /><ChartSkeleton /></>
          ) : (
            <>
              <Suspense fallback={<ChartSkeleton />}>
                <RatingEvolutionChart data={granularEvolution?.buckets ?? []} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <NPSEvolutionChart data={granularEvolution?.buckets ?? []} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <RatedBreakdownChart data={granularEvolution?.buckets ?? []} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <ARTEvolutionChart data={granularEvolution?.buckets ?? []} />
              </Suspense>
            </>
          )}
        </div>

        {/* Agent contribution */}
        {executive.loading && !executive.agents ? (
          <ChartSkeleton />
        ) : (
          <Suspense fallback={<ChartSkeleton />}>
            <AgentContribution agents={executive.agents?.items ?? []} />
          </Suspense>
        )}
      </div>
    );
  }

  // ── Executive tab ───────────────────────────────────────────────────────
  if (tab === "executive") {
    return (
      <div className="space-y-4">
        {header}

        {/* DepartmentAgents always renders */}
        <DepartmentAgents
          department={selectedDept}
          agents={agentList}
          activeNames={executive.agents?.items?.map((a) => a.name)}
        />

        {/* DOW + Hourly bar — side by side */}
        <div className="grid gap-4 lg:grid-cols-2">
          <DowChart
            items={dowItems}
            total={dowTotal}
            maxValue={dowMax}
            loading={executive.loading && !executive.dow}
          />
          {executive.loading && !executive.heatmap ? (
            <ChartSkeleton />
          ) : (
            <Suspense fallback={<ChartSkeleton />}>
              <HourlyBarChart data={executive.heatmap} />
            </Suspense>
          )}
        </div>

        {/* NPS + Notas — independent skeletons */}
        <div className="grid gap-4 lg:grid-cols-2">
          {executive.loading && !executive.quality ? (
            <><ChartSkeleton /><ChartSkeleton /></>
          ) : (
            <>
              <Suspense fallback={<ChartSkeleton />}>
                <NPSCard breakdown={executive.quality?.nps_breakdown ?? null} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <NotasCard rating={executive.quality?.rating ?? null} />
              </Suspense>
            </>
          )}
        </div>

        {/* ART Distribution + Returners — independent skeletons */}
        <div className="grid gap-4 lg:grid-cols-2">
          {executive.loading && !executive.artDistribution ? (
            <><ChartSkeleton /><ChartSkeleton /></>
          ) : (
            <>
              <Suspense fallback={<ChartSkeleton />}>
                <ARTDistribution data={executive.artDistribution} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <ReturnersCard data={executive.returners} />
              </Suspense>
            </>
          )}
        </div>
      </div>
    );
  }

  // ── Mapa Geral tab ──────────────────────────────────────────────────────
  if (tab === "heatmap") {
    return (
      <div className="space-y-4">
        {header}

        {/* Motivos + Ocorrências — first row */}
        {executive.loading && !executive.motives ? (
          <ChartSkeleton />
        ) : (
          <Suspense fallback={<ChartSkeleton />}>
            <DemandBars
              motives={executive.motives}
              occurrences={executive.occurrences}
              dow={executive.dow}
              hideDOW
            />
          </Suspense>
        )}

        {/* Heatmap — compact height */}
        {executive.loading && !executive.heatmap ? (
          <ChartSkeleton />
        ) : (
          <Suspense fallback={<ChartSkeleton />}>
            <HourlyChart data={executive.heatmap} />
          </Suspense>
        )}
      </div>
    );
  }

  // ── BSC tab ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {header}
      {(() => {
        if (!selectedDept) {
          return (
            <EmptyState
              icon={<AlertCircle className="h-12 w-12 text-muted-foreground" />}
              title="Selecione um departamento"
              description="Cada setor possui seu próprio BSC. Use o filtro acima para selecionar um departamento."
            />
          );
        }
        if (bscScorecard.loading) {
          return <TableSkeleton rows={8} />;
        }
        if (bscScorecard.error) {
          return <EmptyState
            icon={<AlertCircle className="h-12 w-12 text-destructive" />}
            title="Erro ao carregar BSC"
            description={bscScorecard.error}
          />;
        }
        if (!bscScorecard.scorecard?.has_config) {
          return (
            <EmptyState
              icon={<AlertCircle className="h-12 w-12 text-muted-foreground" />}
              title="BSC não configurado"
              description={`O departamento "${selectedDept}" ainda não possui um BSC configurado. Configure as métricas no arquivo business_bsc.yaml.`}
            />
          );
        }
        return (
          <Suspense fallback={<TableSkeleton rows={8} />}>
            <BSCScorecardTable
              data={bscScorecard.scorecard}
            />
          </Suspense>
        );
      })()}
    </div>
  );
}

// ── Outer page component (Suspense wrapper for useSearchParams) ─────────────

export default function DashboardPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <DashboardContent />
    </Suspense>
  );
}
