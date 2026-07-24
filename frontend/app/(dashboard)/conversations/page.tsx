"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useConversations, downloadConversationPdf } from "@/hooks/useConversations";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { SortIcon } from "@/components/ui/sort-icon";
import { NPSBadge, RatingBadge, ArtBadge } from "@/components/ui/metric-badge";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { DepartmentMultiSelect } from "@/components/dashboard/department-multi-select";
import { Search, ChevronLeft, ChevronRight, Download, Columns3, ChevronDown, Eye, Archive, FileText, Inbox, Loader2 } from "lucide-react";
import { downloadCsv, cn, ymd } from "@/lib/utils";
import api from "@/lib/api";
import { toast } from "sonner";
import type { ConversationItem, ConversationListResponse } from "@/types";

const PAGE_SIZES = [10, 20, 50, 100];
const EXPORT_PER_PAGE = 10000;

interface ColumnDef {
  key: string;
  label: string;
  sortable: boolean;
  render: (conv: ConversationItem) => React.ReactNode;
}

const START_DATE = ymd(new Date(Date.now() - 29 * 864e5));

const ALL_COLUMNS: ColumnDef[] = [
  { key: "contact", label: "Contato", sortable: true, render: (c) => (
    <div>
      <Link href={`/conversations/${c.id}`} className="font-medium hover:underline">
        {c.contact || "Desconhecido"}
      </Link>
      <div className="text-xs text-muted-foreground">{c.phone}</div>
    </div>
  )},
  { key: "agent", label: "Agente", sortable: true, render: (c) => <span>{c.agent || "—"}</span> },
  { key: "department", label: "Departamento", sortable: false, render: (c) => <span>{c.department || "—"}</span> },
  { key: "msg_count", label: "Msgs", sortable: true, render: (c) => <span className="text-right tabular-nums">{c.msg_count}</span> },
  { key: "rating", label: "Nota (Agente)", sortable: true, render: (c) => <div className="text-right"><RatingBadge value={c.rating} /></div> },
  { key: "nps", label: "NPS", sortable: true, render: (c) => <div className="text-right"><NPSBadge value={c.nps} /></div> },
  { key: "art_minutes", label: "ART (min)", sortable: true, render: (c) => <div className="text-right"><ArtBadge value={c.art_minutes} /></div> },
  { key: "start_time", label: "Data", sortable: true, render: (c) => (
    <span className="text-xs text-muted-foreground">
      {c.start_time ? new Date(c.start_time).toLocaleDateString("pt-BR") : "—"}
    </span>
  )},
];

const DEFAULT_VISIBLE = new Set(["contact", "agent", "department", "msg_count", "rating", "nps", "art_minutes", "start_time"]);

function fmtDate(val: string | null | undefined): string {
  if (!val) return "";
  try { return new Date(val).toLocaleDateString("pt-BR"); } catch { return val; }
}

function fmtNum(val: number | null | undefined, decimals = 0): number | string {
  if (val == null || !Number.isFinite(val)) return "";
  return decimals > 0 ? Number(val.toFixed(decimals)) : val;
}

function buildExportFilters(
  search: string, selectedDept: string, channel: string, statusFilter: string,
  startDate: string, endDate: string,
) {
  const qs = new URLSearchParams();
  qs.set("per_page", String(EXPORT_PER_PAGE));
  qs.set("page", "1");
  qs.set("sort_by", "start_time");
  qs.set("sort_order", "desc");
  if (search) qs.set("search", search);
  if (selectedDept) qs.set("department", selectedDept);
  if (channel) qs.set("channel", channel);
  if (statusFilter) qs.set("status", statusFilter);
  qs.set("start_date", startDate);
  qs.set("end_date", endDate);
  return qs.toString();
}

async function fetchAllForExport(
  search: string, selectedDept: string, channel: string, statusFilter: string,
  startDate: string, endDate: string,
): Promise<ConversationItem[]> {
  const qs = buildExportFilters(search, selectedDept, channel, statusFilter, startDate, endDate);
  const { data } = await api.get<ConversationListResponse>(`/api/v1/conversations/?${qs}`);
  return data.conversations;
}

export default function ConversationsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("");
  const [channel, setChannel] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [startDate, setStartDate] = useState(START_DATE);
  const [endDate, setEndDate] = useState(ymd(new Date()));
  const [sortBy, setSortBy] = useState<string>("start_time");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [columnMenuOpen, setColumnMenuOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(DEFAULT_VISIBLE);
  const [exporting, setExporting] = useState<string | null>(null);

  const filters = {
    page,
    per_page: pageSize,
    search: search || undefined,
    department: selectedDept || undefined,
    channel: channel || undefined,
    status: statusFilter || undefined,
    start_date: startDate,
    end_date: endDate,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  const { data, loading, error, refetch } = useConversations(filters);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;
  const hasData = (data?.total ?? 0) > 0;

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

  async function handleExportCsv() {
    if (!hasData) return;
    setExporting("csv");
    try {
      const all = await fetchAllForExport(search, selectedDept, channel, statusFilter, startDate, endDate);
      downloadCsv(
        all.map((c) => ({ ...c })),
        [
          { key: "contact", label: "Contato" },
          { key: "phone", label: "Telefone" },
          { key: "agent", label: "Agente" },
          { key: "department", label: "Departamento" },
          { key: "msg_count", label: "Mensagens" },
          { key: "rating", label: "Nota (Agente)", format: (v) => (v != null ? String(v) : "") },
          { key: "nps", label: "NPS", format: (v) => (v != null ? Number(v).toFixed(0) : "") },
          { key: "art_minutes", label: "ART (min)", format: (v) => (v != null ? Number(v).toFixed(1) : "") },
          { key: "start_time", label: "Data" },
        ],
        `conversas_${startDate}_${endDate}.csv`,
      );
      toast.success(`CSV exportado com ${all.length} conversas`);
    } catch {
      toast.error("Erro ao exportar CSV");
    } finally {
      setExporting(null);
    }
  }

  async function handleExportXlsx() {
    if (!hasData) return;
    setExporting("xlsx");
    try {
      const all = await fetchAllForExport(search, selectedDept, channel, statusFilter, startDate, endDate);
      const ExcelJS = await import("exceljs");
      const wb = new ExcelJS.Workbook();
      wb.creator = "MBird Dashboard";
      wb.created = new Date();
      const ws = wb.addWorksheet("Conversas");

      const headerBlue = "1A3A5C";
      const headerWhite = "FFFFFF";
      const altRow = "F3F6FA";
      const borderStyle = { style: "thin" as const, color: { argb: "D0D5DD" } };
      const allBorders = { top: borderStyle, bottom: borderStyle, left: borderStyle, right: borderStyle };
      const headerFont = { bold: true, color: { argb: headerWhite }, size: 11 };
      const headerFill = { type: "pattern" as const, pattern: "solid" as const, fgColor: { argb: headerBlue } };
      const altFill = { type: "pattern" as const, pattern: "solid" as const, fgColor: { argb: altRow } };

      ws.columns = [
        { header: "Contato", key: "contact", width: 24 },
        { header: "Telefone", key: "phone", width: 18 },
        { header: "Agente", key: "agent", width: 22 },
        { header: "Departamento", key: "department", width: 18 },
        { header: "Mensagens", key: "msg_count", width: 11 },
        { header: "Nota (Agente)", key: "rating", width: 14 },
        { header: "NPS", key: "nps", width: 8 },
        { header: "ART (min)", key: "art_minutes", width: 12 },
        { header: "Data", key: "start_time", width: 14 },
      ];

      const rows = all.map((c) => ({
        contact: c.contact || "",
        phone: c.phone || "",
        agent: c.agent || "",
        department: c.department || "",
        msg_count: c.msg_count,
        rating: c.rating ?? "",
        nps: c.nps != null ? Number((c.nps as number).toFixed(0)) : "",
        art_minutes: c.art_minutes != null ? Number((c.art_minutes as number).toFixed(1)) : "",
        start_time: fmtDate(c.start_time),
      }));

      for (const row of rows) {
        ws.addRow(row);
      }

      const lastRow = ws.rowCount;

      for (let r = 1; r <= lastRow; r++) {
        const row = ws.getRow(r);
        if (r === 1) {
          row.font = headerFont;
          row.fill = headerFill;
          row.alignment = { vertical: "middle", horizontal: "center", wrapText: true };
          row.height = 28;
        } else {
          row.alignment = { vertical: "middle" };
          row.height = 22;
          if (r % 2 === 0) {
            row.fill = altFill;
          }
        }
        for (let c = 1; c <= 9; c++) {
          const cell = row.getCell(c);
          cell.border = allBorders;
          if (r === 1) continue;
          const colKey = ws.columns[c - 1]?.key;
          if (colKey === "msg_count" || colKey === "rating" || colKey === "nps" || colKey === "art_minutes") {
            cell.alignment = { horizontal: "right", vertical: "middle" };
          }
        }
      }

      ws.autoFilter = { from: "A1", to: `I${lastRow}` };

      ws.views = [{ state: "frozen", ySplit: 1 }];

      const buf = await wb.xlsx.writeBuffer();
      const blob = new Blob([buf], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `conversas_${startDate}_${endDate}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`XLSX exportado com ${all.length} conversas`);
    } catch {
      toast.error("Erro ao exportar XLSX");
    } finally {
      setExporting(null);
    }
  }

  async function handleDownloadPdf(conversationId: string) {
    try {
      await downloadConversationPdf(conversationId);
      toast.success("PDF baixado com sucesso");
    } catch {
      toast.error("Erro ao baixar PDF");
    }
  }

  const selectCls = "h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground shadow-sm";

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

        <DepartmentMultiSelect
          selected={selectedDept ? [selectedDept] : []}
          onChange={(v) => { setSelectedDept(v.length > 0 ? v[0] : ""); setPage(1); }}
        />

        <DateRangePicker startDate={startDate} endDate={endDate} onChange={(s, e) => { setStartDate(s); setEndDate(e); setPage(1); }} />

        <select
          value={channel}
          onChange={(e) => { setChannel(e.target.value); setPage(1); }}
          className={selectCls}
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
          className={selectCls}
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
              <div className="absolute right-0 top-full z-20 mt-1 w-44 rounded-md border border-border bg-card p-2 shadow-lg">
                <p className="mb-1 px-2 text-xs font-medium text-muted-foreground">Colunas visíveis</p>
                {ALL_COLUMNS.map((col) => (
                  <label key={col.key} className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-accent cursor-pointer">
                    <input
                      type="checkbox"
                      checked={visibleColumns.has(col.key)}
                      onChange={() => toggleColumn(col.key)}
                      className="h-3.5 w-3.5 rounded border-input"
                    />
                    {col.label}
                  </label>
                ))}
              </div>
            </>
          )}
        </div>

        <select
          value={pageSize}
          onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
          className={selectCls}
        >
          {PAGE_SIZES.map((s) => (
            <option key={s} value={s}>{s}/pág</option>
          ))}
        </select>

        <Button variant="outline" size="sm" onClick={handleExportCsv} disabled={!hasData || !!exporting}>
          {exporting === "csv" ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Download className="mr-1 h-4 w-4" />}
          CSV
        </Button>

        <Button variant="outline" size="sm" onClick={handleExportXlsx} disabled={!hasData || !!exporting}>
          {exporting === "xlsx" ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Download className="mr-1 h-4 w-4" />}
          XLSX
        </Button>

        {selectedIds.size > 0 && (
          <Button variant="outline" size="sm" onClick={handleArchiveSelected}>
            <Archive className="mr-1 h-4 w-4" />
            Arquivar ({selectedIds.size})
          </Button>
        )}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <p className="text-destructive">{error}</p>
      ) : (
        <>
          <div className="glass-card overflow-x-auto rounded-xl">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox checked={allSelected} onCheckedChange={toggleSelectAll} />
                  </TableHead>
                  {ALL_COLUMNS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                    <TableHead
                      key={col.key}
                      className={cn(
                        "cursor-pointer select-none",
                        ["msg_count", "rating", "nps", "art_minutes"].includes(col.key) ? "text-right" : ""
                      )}
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      <span className="inline-flex items-center">
                        {col.label}
                        {col.sortable && <SortIcon column={col.key} sortBy={sortBy} sortOrder={sortOrder} />}
                      </span>
                    </TableHead>
                  ))}
                  <TableHead className="w-16">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.conversations.map((c) => (
                  <TableRow key={c.id} className={selectedIds.has(c.id) ? "bg-muted/50" : ""}>
                    <TableCell>
                      <Checkbox checked={selectedIds.has(c.id)} onCheckedChange={() => toggleSelect(c.id)} />
                    </TableCell>
                    {ALL_COLUMNS.filter((col) => visibleColumns.has(col.key)).map((col) => (
                      <TableCell key={col.key}>{col.render(c)}</TableCell>
                    ))}
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Link href={`/conversations/${c.id}`} className="text-muted-foreground hover:text-foreground">
                          <Eye className="h-4 w-4" />
                        </Link>
                        <button
                          className="text-muted-foreground hover:text-foreground"
                          onClick={() => handleDownloadPdf(c.id)}
                          title="Baixar PDF"
                        >
                          <FileText className="h-4 w-4" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {data?.conversations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={visibleColumns.size + 2} className="h-24 text-center text-muted-foreground">
                      <EmptyState
                        icon={<Inbox className="h-12 w-12" />}
                        title="Nenhuma conversa encontrada"
                        description="Tente ajustar os filtros ou buscar por outro termo."
                      />
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
