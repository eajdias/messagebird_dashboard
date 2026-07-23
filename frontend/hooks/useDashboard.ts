"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  DashboardSummary,
  BSCData,
  KPIResponse,
  EvolutionResponse,
  AgentRankingResponse,
  ChannelResponse,
  GranularEvolutionResponse,
  EvolutionGranularity,
} from "@/types";

interface DashboardState {
  summary: DashboardSummary | null;
  bsc: BSCData | null;
  kpis: KPIResponse | null;
  evolution: EvolutionResponse | null;
  agents: AgentRankingResponse | null;
  channels: ChannelResponse | null;
  granularEvolution: GranularEvolutionResponse | null;
  loading: boolean;
  error: string | null;
}

const GRANULARITY_COUNT: Record<EvolutionGranularity, number> = {
  day: 30,
  week: 12,
  month: 12,
};

export function useDashboard(params?: {
  start_date?: string;
  end_date?: string;
  department?: string;
  months?: number;
  granularity?: EvolutionGranularity;
}) {
  const granularity: EvolutionGranularity = params?.granularity ?? "month";
  const granularCount = GRANULARITY_COUNT[granularity];

  const [state, setState] = useState<DashboardState>({
    summary: null,
    bsc: null,
    kpis: null,
    evolution: null,
    agents: null,
    channels: null,
    granularEvolution: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const qs = new URLSearchParams();
      if (params?.start_date) qs.set("start_date", params.start_date);
      if (params?.end_date) qs.set("end_date", params.end_date);
      if (params?.department) qs.set("department", params.department);
      const q = qs.toString();
      const suffix = q ? `?${q}` : "";

      const deptParam = params?.department ? `&department=${encodeURIComponent(params.department)}` : "";

      const [summaryRes, bscRes, agentsRes, channelsRes, granularEvoRes] =
        await Promise.all([
          api.get<DashboardSummary>(`/api/v1/dashboard/summary${suffix}`),
          api.get<BSCData>(`/api/v1/dashboard/bsc${suffix}`),
          api.get<AgentRankingResponse>("/api/v1/dashboard/agents"),
          api.get<ChannelResponse>("/api/v1/dashboard/channels"),
          api.get<GranularEvolutionResponse>(
            `/api/v1/dashboard/evolution/granular?granularity=${granularity}&count=${granularCount}${deptParam}`
          ),
        ]);

      let kpis: KPIResponse | null = null;
      if (params?.department) {
        const kpiRes = await api.get<KPIResponse>(
          `/api/v1/dashboard/kpis?department=${encodeURIComponent(params.department)}`
        );
        kpis = kpiRes.data;
      }

      setState({
        summary: summaryRes.data,
        bsc: bscRes.data,
        kpis,
        evolution: null,
        agents: agentsRes.data,
        channels: channelsRes.data,
        granularEvolution: granularEvoRes.data,
        loading: false,
        error: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Erro ao carregar dados",
      }));
    }
  }, [params?.start_date, params?.end_date, params?.department, granularity, granularCount]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
