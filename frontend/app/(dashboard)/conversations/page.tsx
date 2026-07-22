"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useConversations } from "@/hooks/useConversations";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, ChevronLeft, ChevronRight, Download, Columns3, ChevronDown, Eye, Archive, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { downloadCsv, cn } from "@/lib/utils";
import type { ConversationItem } from "@/types";

const PAGE_SIZES = [10, 20, 50, 100];

interface ColumnDef {
  key: string;
  label: string;
  sortable: boolean;
  render: (conv: ConversationItem) => React.ReactNode;
}

export default function ConversationsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [channel, setChannel] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortBy, setSortBy] = useState<string>("start_time");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [columnMenuOpen, setColumnMenuOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(["contact", "agent", "channel", "status", "msg_count", "nps", "art_minutes", "start_time"])
  );

  const { data, loading, error, refetch } = useConversations({
    page,
    per_page: pageSize,
    search: search || undefined,
    department: department || undefined,
    channel: channel || undefined,
    status: statusFilter || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  function handleSort(column: string) {
    if (sortBy === column) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
    setPage(1);
  }

  function toggleColumn(key: string) {
    setVisibleColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const allSelected = data ? data.conversations.length > 0 && data.conversations.every((c) => selectedIds.has(c.id)) : false;

  function toggleSelectAll() {
    if (!data) return;
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.conversations.map((c) => c.id)));
    }
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const handleArchiveSelected = useCallback(() => {
    console.log("Archive selected:", Array.from(selectedIds));
    setSelectedIds(new Set());
  }, [selectedIds]);

  function npsBadge(nps: number | null) {
    if (nps == null) return <span className="text-muted-foreground">—</span>;
    const variant = nps >= 50 ? "success" : nps >= 0 ? "warning" : "destructive";
    return <Badge variant={variant}>{nps.toFixed(0)}</Badge>;
  }

  function SortIcon({ column }: { column: string }) {
    if (sortBy !== column) return <ArrowUpDown className="ml-1 h-3 w-3 opacity-40" />;
    return sortOrder === "asc" ? <ArrowUp className="ml-1 h-3 w-3" /> : <ArrowDown className="ml-1 h-3 w-3" />;
  }

  const columns: ColumnDef[] = useMemo(() => [
    { key: "contact", label: "Contato", sortable: true, render: (c) => (
      <div>
        <Link href={`/conversations/${c.id}`} className="font-medium hover:underline">
          {c.contact || "Desconhecido"}
        </Link>
        <div className="text-xs text-muted-foreground">{c.phone}</div>
      </div>
    )},
    { key: "agent", label: "Agente", sortable: true, render: (c) => <span>{c.agent || "—"}</span> },
    { key: "channel", label: "Canal", sortable: true, render: (c) => <span>{c.channel || "—"}</span> },
    { key: "status", label: "Status", sortable: true, render: (c) => (
      <Badge variant={c.status === "active" ? "success" : "secondary"}>
        {c.status === "active" ? "Ativo" : "Arquivado"}
      </Badge>
    )},
    { key: "msg_count", label: "Msgs", sortable: true, render: (c) => <span className="text-right tabular-nums">{c.msg_count}</span> },
    { key: "nps", label: "NPS", sortable: true, render: (c) => <div className="text-right">{npsBadge(c.nps)}</div> },
    { key: "art_minutes", label: "ART (min)", sortable: true, render: (c) => (
      <span className="text-right tabular-nums">{c.art_minutes != null ? c.art_minutes.toFixed(1) : "—"}</span>
    )},
    { key: "start_time", label: "Data", sortable: true, render: (c) => (
      <span className="text-xs text-muted-foreground">
        {c.start_time ? new Date(c.start_time).toLocaleDateString("pt-BR") : "—"}
      </span>
    )},
  ], []);

  function handleExportCsv() {
    if (!data?.conversations.length) return;
    downloadCsv(
      data.conversations.map((c) => ({ ...c })),
      [
        { key: "contact", label: "Contato" },
        { key: "phone", label: "Telefone" },
        { key: "agent", label: "Agente" },
        { key: "channel", label: "Canal" },
        { key: "status", label: "Status" },
        { key: "msg_count", label: "Mensagens" },
        { key: "nps", label: "NPS", format: (v) => (v != null ? Number(v).toFixed(0) : "") },
        { key: "art_minutes", label: "ART (min)", format: (v) => (v != null ? Number(v).toFixed(1) : "") },
        { key: "start_time", label: "Data" },
      ],
      `conversas_${new Date().toISOString().slice(0, 10)}.csv`,
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Conversas</h1>
        <span className="text-sm text-muted-foreground">{data?.total ?? 0} registros</span>
      </div>

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
          value={department}
          onChange={(e) => { setDepartment(e.target.value); setPage(1); }}
          className="h-9 rounded-md border bg-transparent px-3 text-sm"
        >
          <option value="">Dept: Todos</option>
          <option value="Suporte">Suporte</option>
          <option value="Vendas">Vendas</option>
          <option value="Financeiro">Financeiro</option>
        </select>

        <select
          value={channel}
          onChange={(e) => { setChannel(e.target.value); setPage(1); }}
          className="h-9 rounded-md border bg-transparent px-3 text-sm"
        >
          <option value="">Canal: Todos</option>
          <option value="WhatsApp">WhatsApp</option>
          <option value="Messenger">Messenger</option>
          <option value="Instagram">Instagram</option>
          <option value="Telegram">Telegram</option>
          <option value="SMS">SMS</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border bg-transparent px-3 text-sm"
        >
          <option value="">Status: Todos</option>
          <option value="active">Ativo</option>
          <option value="archived">Arquivado</option>
        </select>

        <div className="relative">
          <Button variant="outline" size="sm" onClick={() => setColumnMenuOpen((p) => !p)}>
            <Columns3 className="mr-1 h-4 w-4" />
            Colunas
            <ChevronDown className="ml-1 h-3 w-3" />
          </Button>
          {columnMenuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setColumnMenuOpen(false)} />
              <div className="absolute right-0 top-full z-20 mt-1 w-44 rounded-md border bg-popover p-2 shadow-md">
                <p className="mb-1 px-2 text-xs font-medium text-muted-foreground">Colunas visíveis</p>
                {columns.map((col) => (
                  <label key={col.key} className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent cursor-pointer">
                    <input
                      type="checkbox"
                      checked={visibleColumns.has(col.key)}
                      onChange={() => toggleColumn(col.key)}
                      className="h-3.5 w-3.5 rounded border-gray-300"
                    />
                    {col.label}
                  </label>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            className="h-9 rounded-md border bg-transparent px-2 text-sm"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>{s}/pág</option>
            ))}
          </select>
        </div>

        <Button variant="outline" size="sm" onClick={handleExportCsv} disabled={!data?.conversations.length}>
          <Download className="mr-1 h-4 w-4" />
          CSV
        </Button>

        {selectedIds.size > 0 && (
          <Button variant="outline" size="sm" onClick={handleArchiveSelected}>
            <Archive className="mr-1 h-4 w-4" />
            Arquivar ({selectedIds.size})
          </Button>
        )}
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
                  <TableHead className="w-10">
                    <Checkbox checked={allSelected} onCheckedChange={toggleSelectAll} />
                  </TableHead>
                  {columns.filter((col) => visibleColumns.has(col.key)).map((col) => (
                    <TableHead
                      key={col.key}
                      className={cn(
                        "cursor-pointer select-none",
                        col.key === "msg_count" || col.key === "nps" || col.key === "art_minutes" ? "text-right" : ""
                      )}
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      <span className="inline-flex items-center">
                        {col.label}
                        {col.sortable && <SortIcon column={col.key} />}
                      </span>
                    </TableHead>
                  ))}
                  <TableHead className="w-12">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.conversations.map((c) => (
                  <TableRow key={c.id} className={selectedIds.has(c.id) ? "bg-muted/50" : ""}>
                    <TableCell>
                      <Checkbox checked={selectedIds.has(c.id)} onCheckedChange={() => toggleSelect(c.id)} />
                    </TableCell>
                    {columns.filter((col) => visibleColumns.has(col.key)).map((col) => (
                      <TableCell key={col.key}>{col.render(c)}</TableCell>
                    ))}
                    <TableCell>
                      <Link href={`/conversations/${c.id}`} className="text-muted-foreground hover:text-foreground">
                        <Eye className="h-4 w-4" />
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
                {data?.conversations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={visibleColumns.size + 2} className="h-24 text-center text-muted-foreground">
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
                Página {page} de {totalPages}
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
