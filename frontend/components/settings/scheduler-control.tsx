"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CalendarClock, Play, Square, RefreshCw } from "lucide-react";
import { toast } from "sonner";

interface JobInfo {
  id: string;
  name: string;
  next_run_time: string | null;
}

interface ProfileInfo {
  name: string;
  incremental_minutes?: number;
  messages_days: number;
}

interface SchedulerStatus {
  running: boolean;
  jobs: JobInfo[];
  started_by_user: boolean;
}

interface ProfileResponse {
  active_profile: string;
  sync_enabled: boolean;
  available_profiles: ProfileInfo[];
}

export default function SchedulerControl() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [profileData, setProfileData] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [changingProfile, setChangingProfile] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusRes, profileRes] = await Promise.all([
        api.get<SchedulerStatus>("/api/v1/admin/scheduler/status"),
        api.get<ProfileResponse>("/api/v1/admin/sync/profile"),
      ]);
      setStatus(statusRes.data);
      setProfileData(profileRes.data);
    } catch {
      // handled by api interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchStatus();
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

  const changeProfile = async (profile: string) => {
    setChangingProfile(true);
    try {
      const { data } = await api.put<{ message: string }>("/api/v1/admin/scheduler/profile", {
        profile,
      });
      toast.success(data.message || `Perfil alterado para "${profile}"`);
      await fetchStatus();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao alterar perfil");
    } finally {
      setChangingProfile(false);
    }
  };

  const formatProfile = (p: ProfileInfo) => {
    const parts = [`${p.messages_days}d msgs`];
    if (p.incremental_minutes) parts.push(`a cada ${p.incremental_minutes}min`);
    else parts.push("sem incremental");
    return parts.join(", ");
  };

  return (
    <Card variant="glass">
      <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <CalendarClock className="h-4 w-4" />
            Sincronização Automática
          </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {loading ? (
          <div className="flex justify-center py-4">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Status</span>
              <Badge variant={status?.running ? "success" : "secondary"}>
                {status?.running ? "Ativo" : "Parado"}
              </Badge>
            </div>

            {profileData && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Perfil</span>
                <Select
                  value={profileData.active_profile}
                  onValueChange={changeProfile}
                  disabled={changingProfile}
                >
                  <SelectTrigger className="h-7 w-[140px] text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {profileData.available_profiles.map((p) => (
                      <SelectItem key={p.name} value={p.name} className="text-xs">
                        <span className="font-medium">{p.name}</span>
                        <span className="ml-2 text-muted-foreground">
                          {formatProfile(p)}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {status?.jobs && status.jobs.length > 0 && (
              <div className="space-y-2">
                <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
                  Jobs
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
                  <Square className="mr-1 h-3.5 w-3.5" />
                  {toggling ? "Parando..." : "Parar"}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startScheduler}
                  disabled={toggling}
                  className="text-green-600 border-green-600/30 hover:bg-green-600/10"
                >
                  <Play className="mr-1 h-3.5 w-3.5" />
                  {toggling ? "Iniciando..." : "Iniciar"}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={fetchStatus} disabled={loading}>
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
