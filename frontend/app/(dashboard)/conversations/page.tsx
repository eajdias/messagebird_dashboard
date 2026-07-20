"use client";

import { useState } from "react";
import Link from "next/link";
import { useConversations } from "@/hooks/useConversations";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";

const PAGE_SIZE = 20;

export default function ConversationsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, loading, error } = useConversations({
    page,
    per_page: PAGE_SIZE,
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  function npsBadge(nps: number | null) {
    if (nps == null) return <span className="text-muted-foreground">—</span>;
    const variant = nps >= 50 ? "success" : nps >= 0 ? "warning" : "destructive";
    return <Badge variant={variant}>{nps.toFixed(0)}</Badge>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Conversas</h1>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar conversa..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border bg-transparent px-3 text-sm"
        >
          <option value="">Todos os status</option>
          <option value="active">Ativo</option>
          <option value="archived">Arquivado</option>
        </select>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <p className="text-destructive">{error}</p>
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contato</TableHead>
                  <TableHead>Agente</TableHead>
                  <TableHead>Canal</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Msgs</TableHead>
                  <TableHead className="text-right">NPS</TableHead>
                  <TableHead className="text-right">ART (min)</TableHead>
                  <TableHead>Data</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.conversations.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>
                      <Link href={`/conversations/${c.id}`} className="font-medium hover:underline">
                        {c.contact || "Desconhecido"}
                      </Link>
                      <div className="text-xs text-muted-foreground">{c.phone}</div>
                    </TableCell>
                    <TableCell>{c.agent || "—"}</TableCell>
                    <TableCell>{c.channel || "—"}</TableCell>
                    <TableCell>
                      <Badge variant={c.status === "active" ? "success" : "secondary"}>
                        {c.status === "active" ? "Ativo" : "Arquivado"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{c.msg_count}</TableCell>
                    <TableCell className="text-right">{npsBadge(c.nps)}</TableCell>
                    <TableCell className="text-right">
                      {c.art_minutes != null ? c.art_minutes.toFixed(1) : "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {c.start_time ? new Date(c.start_time).toLocaleDateString("pt-BR") : "—"}
                    </TableCell>
                  </TableRow>
                ))}
                {data?.conversations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                      Nenhuma conversa encontrada
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {data?.total ?? 0} conversas • Página {page} de {totalPages}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
