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
      const qs = new URLSearchParams();
      if (params.start_date) qs.set("start_date", params.start_date);
      if (params.end_date) qs.set("end_date", params.end_date);
      if (params.department) qs.set("department", params.department);
      const q = qs.toString();
      const suffix = q ? `?${q}` : "";

      const baseEndpoints: { key: string; url: string }[] = [
        { key: "summary", url: `/api/v1/dashboard/summary${suffix}` },
        { key: "bsc", url: `/api/v1/dashboard/bsc${suffix}` },
        { key: "agents", url: `/api/v1/dashboard/agents${suffix}` },
        { key: "channels", url: `/api/v1/dashboard/channels${suffix}` },
      ];

      if (params.department) {
        baseEndpoints.push({
          key: "kpis",
          url: `/api/v1/dashboard/kpis?department=${encodeURIComponent(params.department)}`,
        });
      }

      const failures: string[] = [];
      const results: Record<string, unknown> = {};

      await Promise.allSettled(
        baseEndpoints.map(async (ep) => {
          try {
            const res = await api.get(ep.url, { signal });
            results[ep.key] = res.data;
          } catch (err) {
            if (err instanceof DOMException && err.name === "AbortError") return;
            const msg = err instanceof Error ? err.message : String(err);
            failures.push(`${ep.key}${msg ? ` (${msg})` : ""}`);
          }
        }),
      );

      const error =
        failures.length > 0 ? `Falha ao carregar: ${failures.join(", ")}` : null;

      setState((prev) => ({ ...prev, ...results, loading: false, error }));
    },
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
    [params.start_date, params.end_date, params.department, granularity, granularCount, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchBaseData(controller.signal);
    return () => controller.abort();
  }, [fetchBaseData, enabled]);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchGranular(controller.signal);
    return () => controller.abort();
  }, [fetchGranular, enabled]);

  return { ...state, refetch: () => fetchBaseData(new AbortController().signal) };
}
