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
  refresh: () => Promise<void>;
}

export function useBscScorecard({
  department,
  startDate,
  endDate,
  enabled = true,
}: BscScorecardParams & { enabled?: boolean }): BscScorecardState {
  const [scorecard, setScorecard] = useState<BSCScorecardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScorecard = useCallback(
    async (signal: AbortSignal) => {
      if (!department || !enabled) {
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
          `/api/v1/dashboard/bsc/scorecard?${params.toString()}`,
          { signal },
        );
        setScorecard(response.data);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const message = err instanceof Error ? err.message : "Erro ao carregar BSC";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [department, startDate, endDate, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchScorecard(controller.signal);
    return () => controller.abort();
  }, [fetchScorecard, enabled]);

  return { scorecard, loading, error, refresh: () => fetchScorecard(new AbortController().signal) };
}
