"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { AgentItem, DepartmentItem } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Users, Building2 } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/admin/agents"),
      api.get("/api/v1/admin/departments"),
    ]).then(([agentsRes, deptsRes]) => {
      setAgents(agentsRes.data.agents);
      setDepartments(deptsRes.data.departments);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Agentes & Departamentos</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-4 w-4" />
              Agentes ({agents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>ID Bird</TableHead>
                  <TableHead>Grupo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agents.map((a) => (
                  <TableRow key={a.bird_id}>
                    <TableCell className="font-medium">{a.name}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">{a.bird_id}</TableCell>
                    <TableCell>
                      {a.group ? <Badge variant="secondary">{a.group}</Badge> : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4" />
              Departamentos ({departments.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Nome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {departments.map((d) => (
                  <TableRow key={d.dept_id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">{d.dept_id}</TableCell>
                    <TableCell className="font-medium">{d.label}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
