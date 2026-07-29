"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import SchedulerControl from "@/components/settings/scheduler-control";
import { UserManagementCard } from "@/components/settings/user-management-card";
import { RefreshCw, Activity, User, Palette, Download, Calendar } from "lucide-react";
import { toast } from "sonner";

interface HealthInfo {
  status: string;
  database: string;
  version: string;
}

interface SyncInfo {
  last_sync: string | null;
  status: string;
  records_synced: number;
  duration_seconds: number | null;
  error: string | null;
}

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function getAvailableMonths(): { value: string; label: string }[] {
  const now = new Date();
  const months: { value: string; label: string }[] = [];
  // Go back 12 months
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    months.push({
      value: `${year}-${String(month).padStart(2, "0")}`,
      label: `${MONTHS[d.getMonth()]} ${year}`,
    });
  }
  return months;
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [sync, setSync] = useState<SyncInfo | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMonth, setSyncMonth] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [userManagementKey, setUserManagementKey] = useState(0);

  const availableMonths = getAvailableMonths();

  const fetchStatus = useCallback(async () => {
    try {
      const [h, s] = await Promise.all([
        api.get<HealthInfo>("/api/v1/admin/health").then((r) => r.data),
        api.get<SyncInfo>("/api/v1/admin/sync/status").then((r) => r.data),
      ]);
      setHealth(h);
      setSync(s);
    } catch {
      // handled by api interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const triggerFullSyncToday = async () => {
    setSyncing(true);
    try {
      await api.post("/api/v1/admin/sync/trigger", {
        full_sync: true,
        sync_messages: true,
        backfill_surveys: true,
      });
      toast.success("Full sync de hoje concluído!");
      await fetchStatus();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao sincronizar hoje");
    } finally {
      setSyncing(false);
    }
  };

  const triggerMonthSync = async () => {
    if (!selectedMonth) {
      toast.error("Selecione um mês");
      return;
    }
    const [year, month] = selectedMonth.split("-").map(Number);
    setSyncMonth(true);
    try {
      await api.post("/api/v1/admin/sync/trigger", {
        year,
        month,
        full_sync: true,
        sync_messages: true,
        backfill_surveys: true,
      });
      toast.success(`Sincronização de ${MONTHS[month - 1]} ${year} concluída!`);
      await fetchStatus();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao sincronizar mês");
    } finally {
      setSyncMonth(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Configurações</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4" />
              Informações da Conta
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email</span>
              <span className="font-medium">{user?.email ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Função</span>
              <Badge variant={user?.role === "admin" ? "success" : "secondary"}>
                {user?.role === "admin" ? "Administrador" : "Agente"}
              </Badge>
            </div>
            <div className="pt-2 flex gap-2">
              <Button variant="outline" size="sm" onClick={logout}>
                Sair
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4" />
              Status do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {loading ? (
              <div className="flex justify-center py-4">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">API</span>
                  <Badge variant={health?.status === "healthy" ? "success" : "destructive"}>
                    {health?.status === "healthy" ? "Online" : "Offline"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Banco de Dados</span>
                  <Badge variant={health?.database === "connected" ? "success" : "destructive"}>
                    {health?.database === "connected" ? "Conectado" : "Desconectado"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Versão</span>
                  <span>{health?.version ?? "—"}</span>
                </div>
                {sync && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Última Sinc</span>
                      <span>
                        {sync.last_sync
                          ? new Date(sync.last_sync).toLocaleString("pt-BR")
                          : "Nunca"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Registros</span>
                      <span>{sync.records_synced.toLocaleString("pt-BR")}</span>
                    </div>
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sync Controls */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Full Sync Hoje */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <RefreshCw className="h-4 w-4" />
              Sincronização Diária
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              Executa um full sync de hoje: contatos, conversas, mensagens e métricas.
              Use quando precisar atualizar os dados do dia atual imediatamente.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={triggerFullSyncToday}
              disabled={syncing}
              className="w-full"
            >
              <RefreshCw className={`mr-1 h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
              {syncing ? "Sincronizando..." : "Full Sync Hoje"}
            </Button>
          </CardContent>
        </Card>

        {/* Sincronizar Mês Anterior */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4" />
              Dados Anteriores
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              Sincronize meses específicos para backfill de dados históricos.
              Útil para completar dados de meses anteriores que estão incompletos.
            </p>
            <div className="flex gap-2">
              <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                <SelectTrigger className="h-8 flex-1">
                  <SelectValue placeholder="Selecionar mês" />
                </SelectTrigger>
                <SelectContent>
                  {availableMonths.map((m) => (
                    <SelectItem key={m.value} value={m.value} className="text-xs">
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={triggerMonthSync}
                disabled={syncMonth || !selectedMonth}
              >
                <Download className={`mr-1 h-3.5 w-3.5 ${syncMonth ? "animate-spin" : ""}`} />
                {syncMonth ? "Sincronizando..." : "Sincronizar"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Scheduler + User Management */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SchedulerControl />

        {user?.role === "admin" && (
          <UserManagementCard key={userManagementKey} />
        )}
      </div>

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Palette className="h-4 w-4" />
            Aparência
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          O tema claro/escuro pode ser alternado no ícone de sol/lua no TopBar.
        </CardContent>
      </Card>
    </div>
  );
}
