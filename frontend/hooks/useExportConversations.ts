"use client";

import api from "@/lib/api";
import { downloadCsv, ymd } from "@/lib/utils";
import type { ConversationItem, ExportConversationsRequest, ExportConversationsResponse } from "@/types";

export interface ExportFilters {
  startDate: string;
  endDate: string;
  department?: string;
  channel?: string;
  status?: string;
  search?: string;
}

function fmtDate(val: string | null | undefined): string {
  if (!val) return "";
  try { return new Date(val).toLocaleDateString("pt-BR"); } catch { return val; }
}

function buildQs(filters: ExportFilters): string {
  const qs = new URLSearchParams();
  qs.set("sort_by", "start_time");
  qs.set("sort_order", "desc");
  if (filters.search) qs.set("search", filters.search);
  if (filters.department) qs.set("department", filters.department);
  if (filters.channel) qs.set("channel", filters.channel);
  if (filters.status) qs.set("status", filters.status);
  qs.set("start_date", filters.startDate);
  qs.set("end_date", filters.endDate);
  return qs.toString();
}

export async function fetchAllForExport(filters: ExportFilters): Promise<ConversationItem[]> {
  const { data } = await api.get<ConversationItem[]>(
    `/api/v1/conversations/export?${buildQs(filters)}`,
  );
  return data;
}

export async function exportCsv(filters: ExportFilters): Promise<number> {
  const all = await fetchAllForExport(filters);
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
    `conversas_${filters.startDate}_${filters.endDate}.csv`,
  );
  return all.length;
}

export async function exportXlsx(filters: ExportFilters): Promise<number> {
  const all = await fetchAllForExport(filters);
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
  a.download = `conversas_${filters.startDate}_${filters.endDate}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
  return all.length;
}

export async function exportPdfBulk(filters: ExportFilters): Promise<void> {
  const qs = buildQs(filters);
  const response = await api.get(`/api/v1/conversations/export-pdf?${qs}`, {
    responseType: "blob",
  });
  const disposition: string = response.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match ? match[1] : `OS_${ymd(new Date())}.zip`;
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function saveExport(
  filters: ExportFilters,
  format: ExportConversationsRequest["format"],
  saveToHistory: boolean,
): Promise<ExportConversationsResponse> {
  const body: ExportConversationsRequest = {
    format,
    start_date: filters.startDate,
    end_date: filters.endDate,
    department: filters.department,
    channel: filters.channel,
    status: filters.status,
    search: filters.search,
    save_to_history: saveToHistory,
  };

  if (saveToHistory) {
    const { data } = await api.post<ExportConversationsResponse>("/api/v1/reports/export", body);
    return data;
  }

  const response = await api.post("/api/v1/reports/export", body, { responseType: "blob" });
  const reportId = response.headers["x-report-id"] || "export";

  const disposition: string = response.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match ? match[1] : `conversas_${filters.startDate}_${filters.endDate}.${format === "pdf_zip" ? "zip" : format}`;

  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);

  return {
    status: "ok",
    message: "Arquivo baixado",
    report_id: String(reportId),
    download_url: "",
    size_bytes: 0,
    record_count: 0,
  };
}
