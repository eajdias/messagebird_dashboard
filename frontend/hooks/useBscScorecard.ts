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
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchScorecard();
  }, [fetchScorecard]);

  return { scorecard, loading, error, refresh: fetchScorecard };
}
