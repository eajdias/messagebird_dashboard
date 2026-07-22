"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import SchedulerControl from "@/components/settings/scheduler-control";
import { RefreshCw, Activity, User, Palette } from "lucide-react";

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

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [sync, setSync] = useState<SyncInfo | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
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
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const triggerSync = async () => {
    setSyncing(true);
    try {
      await api.post("/api/v1/admin/sync/trigger", { action: "sync_today" });
      await fetchStatus();
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Configurações</h1>

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Informações da Conta
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email ?? "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Função</span>
            <Badge variant="outline">{user?.role ?? "—"}</Badge>
          </div>
          <div className="pt-2">
            <Button variant="outline" size="sm" onClick={logout}>
              Sair
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Status do Sistema
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {loading ? (
            <div className="flex justify-center py-4">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
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
              {sync && (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Última Sincronização</span>
                    <span>
                      {sync.last_sync
                        ? new Date(sync.last_sync).toLocaleString("pt-BR")
                        : "Nunca"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Registros Sincronizados</span>
                    <span>{sync.records_synced}</span>
                  </div>
                </>
              )}
              <div className="pt-2">
                <Button variant="outline" size="sm" onClick={triggerSync} disabled={syncing}>
                  <RefreshCw className={`mr-1 h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
                  {syncing ? "Sincronizando..." : "Sincronizar Agora"}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <SchedulerControl />

      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
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
