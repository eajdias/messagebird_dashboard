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
} from "@/types";

interface DashboardState {
  summary: DashboardSummary | null;
  bsc: BSCData | null;
  kpis: KPIResponse | null;
  evolution: EvolutionResponse | null;
  agents: AgentRankingResponse | null;
  channels: ChannelResponse | null;
  loading: boolean;
  error: string | null;
}

export function useDashboard(params?: {
  start_date?: string;
  end_date?: string;
  department?: string;
  months?: number;
}) {
  const [state, setState] = useState<DashboardState>({
    summary: null,
    bsc: null,
    kpis: null,
    evolution: null,
    agents: null,
    channels: null,
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

      const [summaryRes, bscRes, evoRes, agentsRes, channelsRes] =
        await Promise.all([
          api.get<DashboardSummary>(`/api/v1/dashboard/summary${suffix}`),
          api.get<BSCData>(`/api/v1/dashboard/bsc${suffix}`),
          api.get<EvolutionResponse>(
            `/api/v1/dashboard/evolution?months=${params?.months ?? 12}`
          ),
          api.get<AgentRankingResponse>("/api/v1/dashboard/agents"),
          api.get<ChannelResponse>("/api/v1/dashboard/channels"),
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
        evolution: evoRes.data,
        agents: agentsRes.data,
        channels: channelsRes.data,
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
  }, [params?.start_date, params?.end_date, params?.department, params?.months]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
