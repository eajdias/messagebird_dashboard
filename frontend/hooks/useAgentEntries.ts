"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  AgentDetailResponse,
  AgentManualEntryCreate,
  AgentManualEntryResponse,
  AgentManualEntryUpdate,
} from "@/types";

interface UseAgentEntriesState {
  detail: AgentDetailResponse | null;
  entries: AgentManualEntryResponse[];
  loading: boolean;
  error: string | null;
  creating: boolean;
  createEntry: (payload: AgentManualEntryCreate) => Promise<void>;
  updateEntry: (id: number, payload: AgentManualEntryUpdate) => Promise<void>;
  deleteEntry: (id: number) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useAgentEntries(agentName: string): UseAgentEntriesState {
  const [detail, setDetail] = useState<AgentDetailResponse | null>(null);
  const [entries, setEntries] = useState<AgentManualEntryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const fetchAll = useCallback(async () => {
    if (!agentName) return;

    setLoading(true);
    setError(null);
    try {
      const [detailRes, entriesRes] = await Promise.all([
        api.get<AgentDetailResponse>(
          `/api/v1/admin/agents/${encodeURIComponent(agentName)}`
        ),
        api.get<AgentManualEntryResponse[]>(
          `/api/v1/admin/agents/${encodeURIComponent(agentName)}/manual-entries`
        ),
      ]);
      setDetail(detailRes.data);
      setEntries(entriesRes.data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Erro ao carregar dados do agente";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [agentName]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchAll();
  }, [fetchAll]);

  const createEntry = useCallback(
    async (payload: AgentManualEntryCreate) => {
      setCreating(true);
      try {
        await api.post(
          `/api/v1/admin/agents/${encodeURIComponent(agentName)}/manual-entries`,
          payload
        );
        await fetchAll();
      } finally {
        setCreating(false);
      }
    },
    [agentName, fetchAll]
  );

  const updateEntry = useCallback(
    async (id: number, payload: AgentManualEntryUpdate) => {
      await api.put(
        `/api/v1/admin/agents/${encodeURIComponent(agentName)}/manual-entries/${id}`,
        payload
      );
      await fetchAll();
    },
    [agentName, fetchAll]
  );

  const deleteEntry = useCallback(
    async (id: number) => {
      await api.delete(
        `/api/v1/admin/agents/${encodeURIComponent(agentName)}/manual-entries/${id}`
      );
      await fetchAll();
    },
    [agentName, fetchAll]
  );

  return {
    detail,
    entries,
    loading,
    error,
    creating,
    createEntry,
    updateEntry,
    deleteEntry,
    refresh: fetchAll,
  };
}
