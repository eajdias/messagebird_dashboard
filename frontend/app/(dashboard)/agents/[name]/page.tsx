"use client";

import { useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAgentEntries } from "@/hooks/useAgentEntries";
import type { AgentManualEntryCreate } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { format, startOfMonth, endOfMonth } from "date-fns";
import { ptBR } from "date-fns/locale";
import { ArrowLeft, Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentName = decodeURIComponent(String(params.name));

  const {
    detail,
    entries,
    loading,
    error,
    creating,
    createEntry,
    updateEntry,
    deleteEntry,
  } = useAgentEntries(agentName);

  // Form state
  const [formDate, setFormDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [formMetric, setFormMetric] = useState("");
  const [formValue, setFormValue] = useState("");
  const [formNotes, setFormNotes] = useState("");

  // Edit dialog state
  const [editId, setEditId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // Delete confirmation
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const handleCreate = async () => {
    if (!formMetric || !formDate || !formValue || !detail) return;

    const payload: AgentManualEntryCreate = {
      department: detail.group,
      metric_name: formMetric,
      entry_date: formDate,
      value: parseFloat(formValue.replace(",", ".")),
    };
    if (formNotes.trim()) {
      payload.notes = formNotes.trim();
    }

    try {
      await createEntry(payload);
      setFormValue("");
      setFormNotes("");
      toast.success("Métrica adicionada com sucesso");
    } catch {
      toast.error("Erro ao adicionar métrica");
    }
  };

  const handleUpdate = async () => {
    if (editId === null || !editValue) return;
    try {
      await updateEntry(editId, { value: parseFloat(editValue.replace(",", ".")) });
      setEditId(null);
      toast.success("Métrica atualizada");
    } catch {
      toast.error("Erro ao atualizar métrica");
    }
  };

  const handleDelete = async () => {
    if (deleteId === null) return;
    try {
      await deleteEntry(deleteId);
      setDeleteId(null);
      toast.success("Métrica removida");
    } catch {
      toast.error("Erro ao remover métrica");
    }
  };

  // Monthly summary
  const monthSummary = useMemo(() => {
    const now = new Date();
    const start = startOfMonth(now);
    const end = endOfMonth(now);
    const summary: Record<string, number> = {};

    for (const e of entries) {
      const d = new Date(e.entry_date + "T00:00:00");
      if (d >= start && d <= end) {
        summary[e.metric_name] = (summary[e.metric_name] || 0) + e.value;
      }
    }
    return summary;
  }, [entries]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">{error || "Agente não encontrado"}</p>
        <Button variant="outline" onClick={() => router.push("/agents")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar para Agentes
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push("/agents")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{detail.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="secondary">{detail.group}</Badge>
            <span className="text-xs text-muted-foreground font-mono">{detail.bird_id}</span>
          </div>
        </div>
      </div>

      {/* Create Form */}
      <Card variant="glass">
        <CardHeader className="py-3">
          <CardTitle className="text-base">Nova Métrica Manual</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="date">Data</Label>
              <Input
                id="date"
                type="date"
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="metric">Métrica</Label>
              <Select value={formMetric} onValueChange={setFormMetric}>
                <SelectTrigger id="metric">
                  <SelectValue placeholder="Selecione..." />
                </SelectTrigger>
                <SelectContent>
                  {detail.available_metrics.map((m) => (
                    <SelectItem key={m.name} value={m.name}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="value">Quantidade</Label>
              <Input
                id="value"
                type="number"
                step="any"
                value={formValue}
                onChange={(e) => setFormValue(e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="notes">Observação</Label>
              <Input
                id="notes"
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                placeholder="Opcional"
              />
            </div>
            <Button
              onClick={handleCreate}
              disabled={creating || !formMetric || !formDate || !formValue}
              className="gap-1.5"
            >
              {creating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Adicionar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Summary */}
      {Object.keys(monthSummary).length > 0 && (
        <Card variant="glass">
          <CardHeader className="py-3">
            <CardTitle className="text-base">
              Resumo — {format(new Date(), "MMMM/yyyy", { locale: ptBR })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(monthSummary).map(([metric, total]) => (
                <div
                  key={metric}
                  className="flex items-center justify-between rounded-lg border border-border/40 bg-muted/30 px-4 py-3"
                >
                  <span className="text-sm font-medium truncate">{metric}</span>
                  <span className="text-lg font-bold tabular-nums text-primary ml-4">
                    {total}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Entries Table */}
      <Card variant="glass">
        <CardHeader className="py-3">
          <CardTitle className="text-base">
            Entradas ({entries.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {entries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-2">
              <Plus className="h-8 w-8 opacity-40" />
              <p className="text-sm">Nenhuma métrica manual cadastrada</p>
              <p className="text-xs">Use o formulário acima para adicionar</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead>Métrica</TableHead>
                    <TableHead className="text-right">Quantidade</TableHead>
                    <TableHead>Observação</TableHead>
                    <TableHead className="w-[80px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="font-mono text-xs">
                        {format(new Date(e.entry_date + "T00:00:00"), "dd/MM/yyyy")}
                      </TableCell>
                      <TableCell className="font-medium text-sm">{e.metric_name}</TableCell>
                      <TableCell className="text-right tabular-nums font-bold">
                        {e.value}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                        {e.notes || "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => {
                              setEditId(e.id);
                              setEditValue(String(e.value));
                              setEditNotes(e.notes || "");
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-600"
                            onClick={() => setDeleteId(e.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editId !== null} onOpenChange={(open) => !open && setEditId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Métrica</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-value">Quantidade</Label>
              <Input
                id="edit-value"
                type="number"
                step="any"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditId(null)}>
              Cancelar
            </Button>
            <Button onClick={handleUpdate}>Salvar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar exclusão</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Tem certeza que deseja remover esta métrica? Esta ação não pode ser desfeita.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="h-4 w-4 mr-2" />
              Remover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
