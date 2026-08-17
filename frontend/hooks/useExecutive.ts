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

type ExecutiveView = "overview" | "executive";

interface ExecutiveParams {
  startDate: string;
  endDate: string;
  selectedDept?: string;
  group?: string;
  view?: ExecutiveView;
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

const OVERVIEW_ENDPOINTS = [
  { key: "meta", url: "/api/v1/dashboard/executive/meta" },
  { key: "quality", url: "/api/v1/dashboard/executive/quality" },
  { key: "agents", url: "/api/v1/dashboard/executive/agents" },
  { key: "returners", url: "/api/v1/dashboard/executive/returners" },
];

const EXECUTIVE_ENDPOINTS = [
  { key: "meta", url: "/api/v1/dashboard/executive/meta" },
  { key: "quality", url: "/api/v1/dashboard/executive/quality" },
  { key: "heatmap", url: "/api/v1/dashboard/executive/heatmap" },
  { key: "motives", url: "/api/v1/dashboard/executive/motives" },
  { key: "occurrences", url: "/api/v1/dashboard/executive/occurrences" },
  { key: "dow", url: "/api/v1/dashboard/executive/dow" },
  { key: "departments", url: "/api/v1/dashboard/executive/departments" },
  { key: "agents", url: "/api/v1/dashboard/executive/agents" },
  { key: "bsc", url: "/api/v1/dashboard/executive/bsc" },
  { key: "artDistribution", url: "/api/v1/dashboard/executive/art-distribution" },
  { key: "returners", url: "/api/v1/dashboard/executive/returners" },
];

export function useExecutive(params: ExecutiveParams & { enabled?: boolean }) {
  const enabled = params.enabled ?? true;
  const view: ExecutiveView = params.view ?? "overview";
  const [state, setState] = useState<ExecutiveState>(INITIAL_STATE);

  const fetchData = useCallback(
    async (signal: AbortSignal) => {
      if (!enabled) return;
      setState((prev) => ({ ...prev, loading: true, error: null }));
      const q = buildQuery(params);
      const qBsc = buildQuery(params, false);

      const endpointDefs = view === "executive" ? EXECUTIVE_ENDPOINTS : OVERVIEW_ENDPOINTS;
      const endpoints = endpointDefs.map((ep) => ({
        key: ep.key,
        url: ep.key === "bsc" ? `${ep.url}${qBsc}` : `${ep.url}${q}`,
      }));

      const failures: string[] = [];
      const results: Record<string, unknown> = {};

      await Promise.allSettled(
        endpoints.map(async (ep) => {
          try {
            const res = await api.get(ep.url, { signal });
            results[ep.key] = res.data;
          } catch (err) {
            if (err instanceof DOMException && err.name === "AbortError") return;
            const msg = _errorReason(err);
            failures.push(`${ep.key}${msg ? ` (${msg})` : ""}`);
          }
        }),
      );

      const error =
        failures.length > 0 ? `Falha ao carregar: ${failures.join(", ")}` : null;

      setState((prev) => ({ ...prev, ...results, loading: false, error }));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [params.startDate, params.endDate, params.selectedDept, params.group, view, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData(controller.signal);
    return () => controller.abort();
  }, [fetchData, enabled]);

  return { ...state, refetch: () => fetchData(new AbortController().signal) };
}

function _errorReason(err: unknown): string {
  if (err instanceof DOMException && err.name === "AbortError") return "";
  if (err && typeof err === "object" && "response" in err) {
    const r = (err as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (r?.data?.detail) return `${r.status} — ${r.data.detail}`;
    if (r?.status) return String(r.status);
  }
  if (err instanceof Error) return err.message;
  return "";
}

export type { ExecutiveParams };
