"use client";

import { useState } from "react";
import api from "@/lib/api";
import type { AvailableReportItem, GenerateReportResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Download, FileBarChart, Loader2 } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<AvailableReportItem[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [type, setType] = useState<"monthly" | "annual">("monthly");
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState("");

  async function loadReports() {
    setLoadingList(true);
    try {
      const { data } = await api.get("/api/v1/reports/available");
      setReports(data.reports);
    } finally {
      setLoadingList(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    setMessage("");
    try {
      const { data } = await api.post<GenerateReportResponse>("/api/v1/reports/generate", {
        type,
        year,
        month: type === "monthly" ? month : undefined,
      });
      setMessage(`Relatório ${data.report_id} gerado com sucesso!`);
      loadReports();
    } catch {
      setMessage("Erro ao gerar relatório");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Relatórios</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Gerar Relatório</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium">Tipo</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as "monthly" | "annual")}
                className="h-9 rounded-md border bg-transparent px-3 text-sm"
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
            <Button variant="outline" onClick={loadReports} disabled={loadingList}>
              Listar Relatórios
            </Button>
          </div>
          {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
        </CardContent>
      </Card>

      {reports.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Relatórios Disponíveis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {reports.map((r) => (
                <div key={r.report_id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <div className="font-medium">{r.filename || r.report_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {r.type} • {r.year}{r.month ? `/${String(r.month).padStart(2, "0")}` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{r.type}</Badge>
                    <a
                      href={r.report_id}
                      download
                      className="inline-flex items-center justify-center h-9 w-9 rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
                    >
                      <Download className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
