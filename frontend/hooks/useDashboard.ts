"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  DashboardSummary,
  BSCData,
  KPIResponse,
  AgentRankingResponse,
  ChannelResponse,
  GranularEvolutionResponse,
  EvolutionGranularity,
} from "@/types";

interface DashboardState {
  summary: DashboardSummary | null;
  bsc: BSCData | null;
  kpis: KPIResponse | null;
  agents: AgentRankingResponse | null;
  channels: ChannelResponse | null;
  granularEvolution: GranularEvolutionResponse | null;
  loading: boolean;
  error: string | null;
  granularLoading: boolean;
}

const GRANULARITY_COUNT: Record<EvolutionGranularity, number> = {
  day: 30,
  week: 12,
  month: 12,
};

export function useDashboard(params: {
  start_date?: string;
  end_date?: string;
  department?: string;
  granularity?: EvolutionGranularity;
  enabled?: boolean;
}) {
  const granularity: EvolutionGranularity = params.granularity ?? "month";
  const granularCount = GRANULARITY_COUNT[granularity];
  const enabled = params.enabled ?? true;

  const [state, setState] = useState<DashboardState>({
    summary: null,
    bsc: null,
    kpis: null,
    agents: null,
    channels: null,
    granularEvolution: null,
    loading: true,
    error: null,
    granularLoading: true,
  });

  const fetchBaseData = useCallback(
    async (signal: AbortSignal) => {
      if (!enabled) return;
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const qs = new URLSearchParams();
        if (params.start_date) qs.set("start_date", params.start_date);
        if (params.end_date) qs.set("end_date", params.end_date);
        if (params.department) qs.set("department", params.department);
        const q = qs.toString();
        const suffix = q ? `?${q}` : "";

        const [summaryRes, bscRes, agentsRes, channelsRes] = await Promise.all([
          api.get<DashboardSummary>(`/api/v1/dashboard/summary${suffix}`, { signal }),
          api.get<BSCData>(`/api/v1/dashboard/bsc${suffix}`, { signal }),
          api.get<AgentRankingResponse>(`/api/v1/dashboard/agents${suffix}`, { signal }),
          api.get<ChannelResponse>(`/api/v1/dashboard/channels${suffix}`, { signal }),
        ]);

        let kpis: KPIResponse | null = null;
        if (params.department) {
          const kpiRes = await api.get<KPIResponse>(
            `/api/v1/dashboard/kpis?department=${encodeURIComponent(params.department)}`,
            { signal },
          );
          kpis = kpiRes.data;
        }

        setState((prev) => ({
          ...prev,
          summary: summaryRes.data,
          bsc: bscRes.data,
          kpis,
          agents: agentsRes.data,
          channels: channelsRes.data,
          loading: false,
          error: null,
        }));
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : "Erro ao carregar dados",
        }));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [params.start_date, params.end_date, params.department, enabled],
  );

  const fetchGranular = useCallback(
    async (signal: AbortSignal) => {
      if (!enabled) return;
      setState((prev) => ({ ...prev, granularLoading: true }));
      try {
        const qs = new URLSearchParams();
        if (params.start_date) qs.set("start_date", params.start_date);
        if (params.end_date) qs.set("end_date", params.end_date);
        if (params.department) qs.set("department", params.department);
        const deptParams = qs.toString();

        const granularEvoRes = await api.get<GranularEvolutionResponse>(
          `/api/v1/dashboard/evolution/granular?granularity=${granularity}&count=${granularCount}${deptParams ? `&${deptParams}` : ""}`,
          { signal },
        );

        setState((prev) => ({
          ...prev,
          granularEvolution: granularEvoRes.data,
          granularLoading: false,
        }));
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setState((prev) => ({ ...prev, granularLoading: false }));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [params.start_date, params.end_date, params.department, granularity, granularCount, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    fetchBaseData(controller.signal);
    return () => controller.abort();
  }, [fetchBaseData, enabled]);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    fetchGranular(controller.signal);
    return () => controller.abort();
  }, [fetchGranular, enabled]);

  return { ...state, refetch: () => fetchBaseData(new AbortController().signal) };
}
