"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  AgentsResponse,
  ARTDistributionResponse,
  DOWResponse,
  DepartmentsResponse,
  ExecutiveBSCResponse,
  ExecutiveMeta,
  HeatmapResponse,
  MotivesResponse,
  OccurrencesResponse,
  QualityResponse,
  ReturnersResponse,
} from "@/types";

interface ExecutiveParams {
  startDate: string;
  endDate: string;
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
  artDistribution: ARTDistributionResponse | null;
  returners: ReturnersResponse | null;
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
  artDistribution: null,
  returners: null,
  loading: true,
  error: null,
};

function buildQuery(params: ExecutiveParams, includeDept = true): string {
  const qs = new URLSearchParams();
  qs.set("start_date", params.startDate);
  qs.set("end_date", params.endDate);
  if (includeDept && params.selectedDept) {
    qs.set("department", params.selectedDept);
  }
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
        artDistribution,
        returners,
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
        api.get<ARTDistributionResponse>(`/api/v1/dashboard/executive/art-distribution${q}`),
        api.get<ReturnersResponse>(`/api/v1/dashboard/executive/returners${q}`),
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
        artDistribution: artDistribution.data,
        returners: returners.data,
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
  }, [params.startDate, params.endDate, params.selectedDept, params.group]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

export type { ExecutiveParams };
