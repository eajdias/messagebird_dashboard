"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  AgentsResponse,
  AgentRow,
  CountedItem,
  DOWResponse,
  DepartmentsResponse,
  DepartmentRow,
  ExecutiveBSCResponse,
  ExecutiveMeta,
  Granularity,
  HeatmapResponse,
  MotivesResponse,
  OccurrencesResponse,
  QualityResponse,
} from "@/types";

interface ExecutiveParams {
  startDate: string;
  endDate: string;
  granularity: Granularity;
  selectedDept?: string;
  group?: string;
}

interface ExecutiveState {
  meta: ExecutiveMeta | null;
  quality: QualityResponse | null;
  heatmap: HeatmapResponse | null;
  motives: MotivesResponse | null;
  occurrences: OccurrencesResponse | null;
  dow: DOWResponse | null;
  departments: DepartmentsResponse | null;
  agents: AgentsResponse | null;
  bsc: ExecutiveBSCResponse | null;
  loading: boolean;
  error: string | null;
}

const INITIAL_STATE: ExecutiveState = {
  meta: null,
  quality: null,
  heatmap: null,
  motives: null,
  occurrences: null,
  dow: null,
  departments: null,
  agents: null,
  bsc: null,
  loading: true,
  error: null,
};

function buildQuery(params: ExecutiveParams, includeDept = true): string {
  const qs = new URLSearchParams();
  qs.set("start_date", params.startDate);
  qs.set("end_date", params.endDate);
  qs.set("granularity", params.granularity);
  if (includeDept && params.selectedDept) {
    qs.set("department", params.selectedDept);
  }
  // BSC still uses group (sector)
  if (params.group) {
    qs.set("group", params.group);
  }
  return `?${qs.toString()}`;
}

export function useExecutive(params: ExecutiveParams) {
  const [state, setState] = useState<ExecutiveState>(INITIAL_STATE);

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    const q = buildQuery(params);
    const qBsc = buildQuery(params, false);

    try {
      const [
        meta,
        quality,
        heatmap,
        motives,
        occurrences,
        dow,
        departments,
        agents,
        bsc,
      ] = await Promise.all([
        api.get<ExecutiveMeta>(`/api/v1/dashboard/executive/meta${q}`),
        api.get<QualityResponse>(`/api/v1/dashboard/executive/quality${q}`),
        api.get<HeatmapResponse>(`/api/v1/dashboard/executive/heatmap${q}`),
        api.get<MotivesResponse>(`/api/v1/dashboard/executive/motives${q}`),
        api.get<OccurrencesResponse>(`/api/v1/dashboard/executive/occurrences${q}`),
        api.get<DOWResponse>(`/api/v1/dashboard/executive/dow${q}`),
        api.get<DepartmentsResponse>(`/api/v1/dashboard/executive/departments${q}`),
        api.get<AgentsResponse>(`/api/v1/dashboard/executive/agents${q}`),
        api.get<ExecutiveBSCResponse>(`/api/v1/dashboard/executive/bsc${qBsc}`),
      ]);

      setState({
        meta: meta.data,
        quality: quality.data,
        heatmap: heatmap.data,
        motives: motives.data,
        occurrences: occurrences.data,
        dow: dow.data,
        departments: departments.data,
        agents: agents.data,
        bsc: bsc.data,
        loading: false,
        error: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Erro ao carregar dados executivos",
      }));
    }
  }, [params.startDate, params.endDate, params.granularity, params.selectedDept, params.group]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export type { ExecutiveParams };

// ── Helpers exposed for the page-level window derivation ────────────────────

export function granularityWindow(granularity: Granularity): { startDate: string; endDate: string } {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const today = `${yyyy}-${mm}-${dd}`;

  if (granularity === "day") {
    return { startDate: today, endDate: today };
  }
  const days = granularity === "week" ? 6 : 29;
  const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
  const sy = start.getFullYear();
  const sm = String(start.getMonth() + 1).padStart(2, "0");
  const sd = String(start.getDate()).padStart(2, "0");
  return { startDate: `${sy}-${sm}-${sd}`, endDate: today };
}
