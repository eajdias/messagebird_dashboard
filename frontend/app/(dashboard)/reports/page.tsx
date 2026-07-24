"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import { ymd } from "@/lib/utils";
import { saveExport, exportReturners, exportArtHigh, exportPdfBulk, type ExportFilters } from "@/hooks/useExportConversations";
import type {
  AvailableReportItem,
  ExportConversationsRequest,
  GenerateReportResponse,
} from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { DepartmentMultiSelect } from "@/components/dashboard/department-multi-select";
import {
  Download, FileBarChart, FileSpreadsheet, FileText, FileArchive,
  Loader2, Inbox, Calendar, Trash2, AlertTriangle, X, Users, Timer,
} from "lucide-react";
import { toast } from "sonner";

const START_DATE = ymd(new Date(Date.now() - 29 * 864e5));

const selectCls = "h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground shadow-sm";

const FORMAT_LABELS: Record<string, string> = {
  csv: "CSV",
  xlsx: "Excel",
  pdf_zip: "ZIP (OS)",
};

const FORMAT_ICONS: Record<string, React.ReactNode> = {
  csv: <Download className="h-4 w-4" />,
  xlsx: <FileSpreadsheet className="h-4 w-4" />,
  pdf_zip: <FileArchive className="h-4 w-4" />,
};

const FORMAT_EXTENSIONS: Record<string, string> = {
  csv: ".csv",
  xlsx: ".xlsx",
  pdf_zip: ".zip",
};

function formatSize(bytes: number | null | undefined): string {
  if (bytes == null || bytes <= 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ReportsPage() {
  const [startDate, setStartDate] = useState(START_DATE);
  const [endDate, setEndDate] = useState(ymd(new Date()));
  const [selectedDept, setSelectedDept] = useState("");
  const [channel, setChannel] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [saveToHistory, setSaveToHistory] = useState(false);
  const [artThreshold, setArtThreshold] = useState(15);

  const [reports, setReports] = useState<AvailableReportItem[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [type, setType] = useState<"monthly" | "annual">("monthly");
  const [year, setYear] = useState(0);
  const [month, setMonth] = useState(0);
  const [mounted, setMounted] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState("");
  const [exporting, setExporting] = useState<string | null>(null);

  const [availableTypeFilter, setAvailableTypeFilter] = useState("");

  async function loadReports() {
    setLoadingList(true);
    try {
      const { data } = await api.get<{ reports: AvailableReportItem[] }>("/api/v1/reports/available");
      setReports(data.reports);
    } catch {
      toast.error("Erro ao carregar relatórios");
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    const now = new Date();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setYear(now.getFullYear());
    setMonth(now.getMonth() + 1);
    setMounted(true);
    loadReports();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setMessage("");
    try {
      const { data } = await api.post<GenerateReportResponse>("/api/v1/reports/generate", {
        type,
        year,
        month: type === "monthly" ? month : undefined,
      });
      toast.success(`Relatório ${data.report_id} gerado com sucesso!`);
      setMessage(`Relatório ${data.report_id} gerado com sucesso!`);
      loadReports();
    } catch {
      toast.error("Erro ao gerar relatório");
    } finally {
      setGenerating(false);
    }
  }

  const filters: ExportFilters = {
    startDate,
    endDate,
    department: selectedDept || undefined,
    channel: channel || undefined,
    status: statusFilter || undefined,
    search: search || undefined,
  };

  async function handleExport(format: ExportConversationsRequest["format"]) {
    setExporting(format);
    try {
      const result = await saveExport(filters, format, saveToHistory);
      if (saveToHistory) {
        toast.success(`${FORMAT_LABELS[format]} salvo no histórico (${result.record_count} registros)`);
        loadReports();
      } else {
        toast.success(`${FORMAT_LABELS[format]} baixado com sucesso`);
      }
    } catch (err) {
      console.error(`${format} export failed`, err);
      toast.error(`Erro ao exportar ${FORMAT_LABELS[format]}`);
    } finally {
      setExporting(null);
    }
  }

  async function handleExportReturners(format: "csv" | "xlsx") {
    setExporting(`returners_${format}`);
    try {
      const result = await exportReturners(filters, format, saveToHistory);
      if (saveToHistory) {
        toast.success(`Retornantes ${format.toUpperCase()} salvo (${result.record_count} contatos)`);
        loadReports();
      } else {
        toast.success(`Retornantes ${format.toUpperCase()} baixado com sucesso`);
      }
    } catch (err) {
      console.error("Returners export failed", err);
      toast.error("Erro ao exportar retornantes");
    } finally {
      setExporting(null);
    }
  }

  async function handleExportArtHigh(format: "csv" | "xlsx") {
    setExporting(`art_${format}`);
    try {
      const result = await exportArtHigh(filters, format, saveToHistory, artThreshold);
      if (saveToHistory) {
        toast.success(`ART > ${artThreshold}min ${format.toUpperCase()} salvo (${result.record_count} registros)`);
        loadReports();
      } else {
        toast.success(`ART > ${artThreshold}min ${format.toUpperCase()} baixado com sucesso`);
      }
    } catch (err) {
      console.error("ART high export failed", err);
      toast.error("Erro ao exportar ART alto");
    } finally {
      setExporting(null);
    }
  }

  async function handleDownload(report: AvailableReportItem) {
    window.open(`/api/v1/reports/${report.report_id}/download`, "_blank");
  }

  async function handleDelete(report: AvailableReportItem) {
    try {
      await api.delete(`/api/v1/reports/${report.report_id}`);
      toast.success("Relatório removido");
      loadReports();
    } catch (err) {
      console.error("Delete failed", err);
      toast.error("Erro ao remover relatório");
    }
  }

  const filteredReports = availableTypeFilter
    ? reports.filter((r) => {
        if (availableTypeFilter === "export") return r.type === "export";
        if (availableTypeFilter === "periodic") return r.type !== "export";
        if (availableTypeFilter === "csv") return r.format === "csv";
        if (availableTypeFilter === "xlsx") return r.format === "xlsx";
        if (availableTypeFilter === "pdf_zip") return r.format === "pdf_zip";
        return true;
      })
    : reports;

  if (!mounted) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Relatórios</h1>
        <Button variant="outline" size="sm" onClick={loadReports} disabled={loadingList}>
          {loadingList ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Atualizar
        </Button>
      </div>

      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            Exportar Dados
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <DepartmentMultiSelect
              selected={selectedDept ? [selectedDept] : []}
              onChange={(v) => setSelectedDept(v.length > 0 ? v[0] : "")}
            />
            <div suppressHydrationWarning>
              <DateRangePicker
                startDate={startDate}
                endDate={endDate}
                onChange={(s, e) => { setStartDate(s); setEndDate(e); }}
              />
            </div>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
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
              onChange={(e) => setStatusFilter(e.target.value)}
              className={selectCls}
            >
              <option value="">Status: Todos</option>
              <option value="active">Ativo</option>
              <option value="archived">Arquivado</option>
            </select>
            <div className="relative flex-1 min-w-[180px] max-w-xs">
              <Input
                placeholder="Buscar..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-3"
              />
              {search && (
                <button
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setSearch("")}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <Checkbox
              id="save-history"
              checked={saveToHistory}
              onCheckedChange={(v) => setSaveToHistory(!!v)}
            />
            <label htmlFor="save-history" className="text-sm text-muted-foreground cursor-pointer select-none">
              Salvar no histórico (disponível para outros usuários)
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mr-1">Exportação geral</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("csv")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "csv" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              CSV (conversas)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("xlsx")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "xlsx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileSpreadsheet className="h-4 w-4" />}
              Excel (conversas)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                setExporting("zip_os");
                try {
                  await exportPdfBulk(filters);
                  toast.success("ZIP das OS baixado com sucesso");
                } catch (err) {
                  console.error("ZIP OS export failed", err);
                  toast.error("Erro ao exportar ZIP das OS");
                } finally {
                  setExporting(null);
                }
              }}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "zip_os" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileArchive className="h-4 w-4" />}
              ZIP (OS)
            </Button>
          </div>

          <div className="border-t border-border my-1" />

          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mr-1">Relatórios específicos</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportReturners("csv")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "returners_csv" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
              Retornantes CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportReturners("xlsx")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "returners_xlsx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
              Retornantes Excel
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1">
              <Timer className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">ART &gt;</span>
              <Input
                type="number"
                min={1}
                value={artThreshold}
                onChange={(e) => setArtThreshold(Math.max(1, Number(e.target.value)))}
                className="h-7 w-16 text-xs px-2"
              />
              <span className="text-xs text-muted-foreground">min</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportArtHigh("csv")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "art_csv" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Timer className="h-4 w-4" />}
              CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportArtHigh("xlsx")}
              disabled={!!exporting}
              className="gap-2"
            >
              {exporting === "art_xlsx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Timer className="h-4 w-4" />}
              Excel
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Gerar Relatório Periódico
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Tipo</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as "monthly" | "annual")}
                className={selectCls}
              >
                <option value="monthly">Mensal</option>
                <option value="annual">Anual</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Ano</label>
              <Input
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="w-24"
              />
            </div>
            {type === "monthly" && (
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium">Mês</label>
                <Input
                  type="number"
                  min={1}
                  max={12}
                  value={month}
                  onChange={(e) => setMonth(Number(e.target.value))}
                  className="w-20"
                />
              </div>
            )}
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileBarChart className="h-4 w-4" />}
              Gerar
            </Button>
          </div>
          {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Relatórios Disponíveis
              {!loadingList && (
                <Badge variant="secondary" className="ml-1">{filteredReports.length}</Badge>
              )}
            </CardTitle>
            <select
              value={availableTypeFilter}
              onChange={(e) => setAvailableTypeFilter(e.target.value)}
              className={selectCls}
            >
              <option value="">Todos os tipos</option>
              <option value="export">Exportações rápidas</option>
              <option value="periodic">Relatórios periódicos</option>
              <option value="csv">CSV</option>
              <option value="xlsx">Excel</option>
              <option value="pdf_zip">ZIP (OS)</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {loadingList ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              {availableTypeFilter ? (
                <>
                  <AlertTriangle className="h-10 w-10 mb-3" />
                  <p className="text-sm font-medium">Nenhum relatório deste tipo</p>
                  <p className="text-xs">Tente outro filtro ou gere um novo relatório.</p>
                </>
              ) : (
                <>
                  <Inbox className="h-10 w-10 mb-3" />
                  <p className="text-sm font-medium">Nenhum relatório disponível</p>
                  <p className="text-xs">Exportações salvas e relatórios periódicos aparecerão aqui.</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredReports.map((r) => (
                <div
                  key={r.report_id}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {r.type === "export" && r.format ? (
                        FORMAT_ICONS[r.format]
                      ) : (
                        <FileBarChart className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="font-medium truncate">
                        {r.filename || r.report_id}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {r.type === "export" ? (
                        <>
                          {r.format ? FORMAT_LABELS[r.format] : "Exportação"}
                          {r.record_count != null && ` • ${r.record_count} registros`}
                          {r.size_bytes != null && ` • ${formatSize(r.size_bytes)}`}
                          {r.start_date && ` • ${r.start_date}`}
                          {r.end_date && r.end_date !== r.start_date && ` — ${r.end_date}`}
                        </>
                      ) : (
                        <>
                          {r.type === "monthly" ? "Mensal" : r.type === "annual" ? "Anual" : r.type}
                          {r.year && ` • ${r.year}`}
                          {r.month != null && `/${String(r.month).padStart(2, "0")}`}
                          {r.group && ` • ${r.group}`}
                        </>
                      )}
                      {r.created_by && ` • ${r.created_by}`}
                      {r.created_at && ` • ${new Date(r.created_at).toLocaleDateString("pt-BR")}`}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    {r.type === "export" && r.format && (
                      <Badge variant="secondary" className="text-xs">
                        {FORMAT_LABELS[r.format]}
                      </Badge>
                    )}
                    {r.type !== "export" && (
                      <Badge variant="secondary" className="text-xs">
                        {r.type}
                      </Badge>
                    )}
                    <button
                      className="inline-flex items-center justify-center h-9 w-9 rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
                      onClick={() => handleDownload(r)}
                      title="Download"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                    <button
                      className="inline-flex items-center justify-center h-9 w-9 rounded-md text-sm font-medium hover:bg-destructive/10 hover:text-destructive transition-colors"
                      onClick={() => handleDelete(r)}
                      title="Remover"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
