"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Users, Plus, Trash2, KeyRound } from "lucide-react";
import { toast } from "sonner";

interface UserItem {
  id: number;
  email: string;
  role: string;
  name: string;
  active: boolean;
}

export function UserManagementCard() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [pwUserId, setPwUserId] = useState<number | null>(null);
  const [pwEmail, setPwEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formRole, setFormRole] = useState("agent");
  const [formName, setFormName] = useState("");

  const fetchUsers = useCallback(async () => {
    try {
      const { data } = await api.get<{ users: UserItem[] }>("/api/v1/admin/users");
      setUsers(data.users);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const createUser = async () => {
    if (!formEmail || !formPassword) {
      toast.error("Email e senha são obrigatórios");
      return;
    }
    try {
      await api.post("/api/v1/admin/users", {
        email: formEmail,
        password: formPassword,
        role: formRole,
        name: formName,
      });
      toast.success("Usuário criado");
      setDialogOpen(false);
      resetForm();
      fetchUsers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao criar usuário");
    }
  };

  const resetForm = () => {
    setFormEmail("");
    setFormPassword("");
    setFormRole("agent");
    setFormName("");
  };

  const changePassword = async () => {
    if (!pwUserId || !newPassword) return;
    try {
      await api.put(`/api/v1/admin/users/${pwUserId}/password`, {
        new_password: newPassword,
      });
      toast.success(`Senha alterada para ${pwEmail}`);
      setPasswordDialogOpen(false);
      setNewPassword("");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao alterar senha");
    }
  };

  const deleteUser = async (userId: number, email: string) => {
    if (!confirm(`Remover usuário "${email}"?`)) return;
    try {
      await api.delete(`/api/v1/admin/users/${userId}`);
      toast.success("Usuário removido");
      fetchUsers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao remover usuário");
    }
  };

  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Gerenciar Usuários
          </span>
          <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) resetForm(); }}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="mr-1 h-3.5 w-3.5" />
                Novo
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Novo Usuário</DialogTitle>
              </DialogHeader>
              <div className="space-y-3 pt-2">
                <div>
                  <Label htmlFor="uemail">Email</Label>
                  <Input id="uemail" type="email" value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="usuario@empresa.com" />
                </div>
                <div>
                  <Label htmlFor="uname">Nome</Label>
                  <Input id="uname" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="Nome completo" />
                </div>
                <div>
                  <Label htmlFor="upass">Senha</Label>
                  <Input id="upass" type="password" value={formPassword} onChange={(e) => setFormPassword(e.target.value)} placeholder="Senha" />
                </div>
                <div>
                  <Label htmlFor="urole">Função</Label>
                  <Select value={formRole} onValueChange={setFormRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="agent">Agente</SelectItem>
                      <SelectItem value="admin">Administrador</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={createUser} className="w-full">
                  Criar Usuário
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {loading ? (
          <div className="flex justify-center py-4">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : users.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2 text-center">Nenhum usuário cadastrado</p>
        ) : (
          users.map((u) => (
            <div key={u.id} className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">{u.email}</span>
                  <Badge variant={u.role === "admin" ? "success" : "secondary"} className="text-[10px] px-1.5 py-0">
                    {u.role === "admin" ? "Admin" : "Agente"}
                  </Badge>
                </div>
                {u.name && <p className="text-xs text-muted-foreground">{u.name}</p>}
              </div>
              <div className="flex items-center gap-1 ml-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => {
                    setPwUserId(u.id);
                    setPwEmail(u.email);
                    setNewPassword("");
                    setPasswordDialogOpen(true);
                  }}
                >
                  <KeyRound className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive"
                  onClick={() => deleteUser(u.id, u.email)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))
        )}

        <Dialog open={passwordDialogOpen} onOpenChange={(o) => { setPasswordDialogOpen(o); if (!o) setNewPassword(""); }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Alterar Senha — {pwEmail}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 pt-2">
              <div>
                <Label htmlFor="npw">Nova Senha</Label>
                <Input id="npw" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Nova senha" />
              </div>
              <Button onClick={changePassword} className="w-full">
                Salvar
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
