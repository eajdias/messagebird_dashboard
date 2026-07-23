"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type { BSCScorecardResponse } from "@/types";

interface BscScorecardParams {
  department: string;
  startDate: string;
  endDate: string;
}

interface BscScorecardState {
  scorecard: BSCScorecardResponse | null;
  loading: boolean;
  error: string | null;
  saveManualValue: (agentName: string, metricName: string, value: number) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useBscScorecard({ department, startDate, endDate }: BscScorecardParams): BscScorecardState {
  const [scorecard, setScorecard] = useState<BSCScorecardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScorecard = useCallback(async () => {
    if (!department) {
      setScorecard(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("department", department);
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);

      const response = await api.get<BSCScorecardResponse>(
        `/api/v1/dashboard/bsc/scorecard?${params.toString()}`
      );
      setScorecard(response.data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao carregar BSC";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [department, startDate, endDate]);

  useEffect(() => {
    fetchScorecard();
  }, [fetchScorecard]);

  const saveManualValue = useCallback(
    async (agentName: string, metricName: string, value: number) => {
      if (!department || !startDate || !endDate) return;

      await api.put("/api/v1/dashboard/bsc/manual-value", {
        department,
        agent_name: agentName,
        metric_name: metricName,
        period_start: startDate,
        period_end: endDate,
        value,
      });

      await fetchScorecard();
    },
    [department, startDate, endDate, fetchScorecard]
  );

  return { scorecard, loading, error, saveManualValue, refresh: fetchScorecard };
}
