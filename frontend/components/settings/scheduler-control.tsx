"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CalendarClock, Play, Square, RefreshCw } from "lucide-react";

interface JobInfo {
  id: string;
  name: string;
  next_run_time: string | null;
}

interface SchedulerStatus {
  running: boolean;
  jobs: JobInfo[];
  started_by_user: boolean;
}

export default function SchedulerControl() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const { data } = await api.get<SchedulerStatus>("/api/v1/admin/scheduler/status");
      setStatus(data);
    } catch {
      // handled by api interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const startScheduler = async () => {
    setToggling(true);
    try {
      await api.post("/api/v1/admin/scheduler/start");
      await fetchStatus();
    } finally {
      setToggling(false);
    }
  };

  const stopScheduler = async () => {
    setToggling(true);
    try {
      await api.post("/api/v1/admin/scheduler/stop");
      await fetchStatus();
    } finally {
      setToggling(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5" />
          Sincronização Agendada
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {loading ? (
          <div className="flex justify-center py-4">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Status</span>
              <Badge variant={status?.running ? "success" : "secondary"}>
                {status?.running ? "Ativo" : "Parado"}
              </Badge>
            </div>

            {status?.jobs && status.jobs.length > 0 && (
              <div className="space-y-2">
                <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
                  Jobs Agendados
                </span>
                {status.jobs.map((job) => (
                  <div key={job.id} className="flex justify-between text-xs bg-muted/50 rounded-md px-3 py-2">
                    <span className="font-medium">{job.name}</span>
                    <span className="text-muted-foreground">
                      {job.next_run_time
                        ? new Date(job.next_run_time).toLocaleString("pt-BR")
                        : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2 pt-1">
              {status?.running ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={stopScheduler}
                  disabled={toggling}
                  className="text-destructive border-destructive/30 hover:bg-destructive/10"
                >
                  <Square className="mr-1 h-4 w-4" />
                  {toggling ? "Parando..." : "Parar Scheduler"}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startScheduler}
                  disabled={toggling}
                  className="text-green-600 border-green-600/30 hover:bg-green-600/10"
                >
                  <Play className="mr-1 h-4 w-4" />
                  {toggling ? "Iniciando..." : "Iniciar Scheduler"}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={fetchStatus} disabled={loading}>
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
            </div>

            <p className="text-xs text-muted-foreground">
              {status?.running
                ? "As sincronizações automáticas estão ativas."
                : "As sincronizações automáticas estão desligadas. Use o botão acima ou a sincronização manual para atualizar dados."}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
