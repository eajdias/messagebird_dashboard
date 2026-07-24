"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import type {
  ConversationListResponse,
  ConversationDetail,
  ConversationMessagesResponse,
} from "@/types";

interface ConversationFilters {
  start_date?: string;
  end_date?: string;
  department?: string;
  agent?: string;
  channel?: string;
  status?: string;
  search?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: string;
}

interface ConversationsState {
  data: ConversationListResponse | null;
  loading: boolean;
  error: string | null;
}

export function useConversations(filters?: ConversationFilters) {
  const [state, setState] = useState<ConversationsState>({
    data: null,
    loading: true,
    error: null,
  });

  const filtersKey = JSON.stringify(filters);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const qs = new URLSearchParams();
      const f = filtersRef.current;
      if (f) {
        Object.entries(f).forEach(([k, v]) => {
          if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
        });
      }
      const q = qs.toString();
      const { data } = await api.get<ConversationListResponse>(
        `/api/v1/conversations/${q ? `?${q}` : ""}`
      );
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Erro ao carregar conversas",
      }));
    }
  }, []);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey]);

  return { ...state, refetch: fetchData };
}

export function useConversation(id: string | null) {
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<ConversationDetail>(`/api/v1/conversations/${id}`)
      .then((res) => {
        setDetail(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Erro");
        setLoading(false);
      });
  }, [id]);

  return { detail, loading, error };
}

export function useConversationMessages(id: string | null) {
  const [state, setState] = useState<ConversationMessagesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .get<ConversationMessagesResponse>(
        `/api/v1/conversations/${id}/messages`
      )
      .then((res) => {
        setState(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Erro");
        setLoading(false);
      });
  }, [id]);

  return { ...state, loading, error };
}

export async function downloadConversationPdf(conversationId: string) {
  const response = await api.get(
    `/api/v1/conversations/${conversationId}/pdf`,
    { responseType: "blob" },
  );
  const disposition: string = response.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match ? match[1] : `OS_${conversationId}.pdf`;
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
