"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import api from "@/lib/api";
import { ymd } from "@/lib/utils";
import { useDashboard } from "@/hooks/useDashboard";
import { useExecutive } from "@/hooks/useExecutive";
import { useBscScorecard } from "@/hooks/useBscScorecard";
import type { EvolutionGranularity, AgentItem } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { SegmentedToggle } from "@/components/ui/segmented-toggle";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { Tabs, readTabFromQuery, type TabOption } from "@/components/ui/tabs";
import { DepartmentMultiSelect } from "@/components/dashboard/department-multi-select";
import { DepartmentAgents } from "@/components/dashboard/department-agents";
import { Button } from "@/components/ui/button";

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

const HourlyChart = dynamic(
  () => import("@/components/dashboard/hourly-chart").then((m) => ({ default: m.HourlyChart })),
  { ssr: false, loading: () => <ChartSkeleton /> }
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

const AgentContribution = dynamic(
  () => import("@/components/dashboard/agent-contribution").then((m) => ({ default: m.AgentContribution })),
  { loading: () => <ChartSkeleton /> }
);

const BSCScorecardTable = dynamic(
  () => import("@/components/dashboard/bsc-scorecard-table").then((m) => ({ default: m.BSCScorecardTable })),
  { loading: () => <TableSkeleton rows={8} /> }
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

// ── Simple stat card ───────────────────────────────────────────────────────

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Card variant="glass">
      <CardHeader className="pb-1"><CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle></CardHeader>
      <CardContent><span className="text-2xl font-bold tabular-nums">{value}</span></CardContent>
    </Card>
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

  const defaultStart = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() - 29);
    return ymd(d);
  }, []);
  const defaultEnd = useMemo(() => ymd(new Date()), []);

  const [startDate, setStartDate] = useState<string>(defaultStart);
  const [endDate, setEndDate] = useState<string>(defaultEnd);

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

  const { granularEvolution, loading, error } = useDashboard({
    granularity,
    start_date: startDate,
    end_date: endDate,
    department: selectedDept || undefined,
  });

  const executive = useExecutive({
    startDate,
    endDate,
    selectedDept: selectedDept || undefined,
    group: "Suporte Tecnico",
  });

  const bscScorecard = useBscScorecard({
    department: selectedDept || "",
    startDate,
    endDate,
  });

  if (!mounted || loading || executive.loading) {
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
        <DepartmentMultiSelect
          selected={selectedDept ? [selectedDept] : []}
          onChange={(v) => setSelectedDept(v.length > 0 ? v[0] : "")}
        />
        <div suppressHydrationWarning>
          <DateRangePicker startDate={startDate} endDate={endDate} onChange={(s, e) => { setStartDate(s); setEndDate(e); }} />
        </div>
      </div>
    </div>
  );

  if (tab === "overview") {
    const nps = executive.quality?.nps_breakdown?.real_nps;
    const pctReturning = executive.returners?.pct_returning;

    return (
      <div className="space-y-6">
        {header}
        <div className="flex items-center gap-3">
          <SegmentedToggle value={granularity} onChange={setGranularity} options={GRANULARITY_OPTIONS} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Chats" value={(executive.meta?.total_chats ?? 0).toLocaleString("pt-BR")} />
          <StatCard title="Mensagens" value={(executive.meta?.total_messages ?? 0).toLocaleString("pt-BR")} />
          <StatCard title="NPS" value={nps != null && Number.isFinite(nps) ? nps.toFixed(1) : "—"} />
          <StatCard title="Retornantes" value={pctReturning != null ? `${pctReturning.toFixed(1)}%` : "—"} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Suspense fallback={<ChartSkeleton />}>
            <RatingEvolutionChart data={granularEvolution?.buckets ?? []} />
          </Suspense>
          <Suspense fallback={<ChartSkeleton />}>
            <NPSEvolutionChart data={granularEvolution?.buckets ?? []} />
          </Suspense>
        </div>

        <Suspense fallback={<ChartSkeleton />}>
          <AgentContribution agents={executive.agents?.items ?? []} />
        </Suspense>
      </div>
    );
  }

  if (tab === "executive") {
    const execLoading = executive.loading;
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
            <div className="grid gap-4 lg:grid-cols-2">
              <Suspense fallback={<ChartSkeleton />}>
                <ARTDistribution data={executive.artDistribution} />
              </Suspense>
              <Suspense fallback={<ChartSkeleton />}>
                <ReturnersCard data={executive.returners} />
              </Suspense>
            </div>
          </>
        )}
      </div>
    );
  }

  // tab === "bsc"
  return (
    <div className="space-y-6">
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
              onSaveManual={bscScorecard.saveManualValue}
            />
          </Suspense>
        );
      })()}
    </div>
  );
}

// ── Outer page component (Suspense wrapper for useSearchParams) ─────────────

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  return (
    <Suspense fallback={<PageLoader />}>
      <DashboardContent mounted={mounted} />
    </Suspense>
  );
}
