"use client";

import { useQuery } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Clock, Ticket, AlertCircle, Loader2 } from "lucide-react";

type Ticket = {
  id: string;
  user_email: string;
  category: string;
  status: string;
  cache_hit: boolean;
  created_at: string;
};

export default function AdminDashboard() {
  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets"],
    queryFn: async () => {
      const res = await fetch("/api/tickets");
      if (!res.ok) throw new Error("Failed to fetch tickets");
      const json = await res.json();
      return json.data as Ticket[];
    },
    // Refetch often for the queue
    refetchInterval: 5000,
  });

  const totalTickets = tickets?.length || 0;
  const autoResolved = tickets?.filter(t => t.cache_hit).length || 0;
  const requiresReview = tickets?.filter(t => !t.cache_hit).length || 0;

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground mt-1">Overview of your helpdesk agent performance.</p>
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tickets Processed</CardTitle>
            <Ticket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTickets}</div>
            <p className="text-xs text-muted-foreground mt-1">Across all categories</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit (Auto-Resolved)</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{autoResolved}</div>
            <p className="text-xs text-muted-foreground mt-1">Directly solved by KB</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Miss (Investigated)</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{requiresReview}</div>
            <p className="text-xs text-muted-foreground mt-1">Full AI investigation pipeline run</p>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-md border-border/50">
        <CardHeader className="bg-muted/30 border-b">
          <CardTitle>Live Ticket Queue</CardTitle>
          <CardDescription>Recent tickets flowing through the system.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/10">
              <TableRow>
                <TableHead className="pl-6">Ticket ID</TableHead>
                <TableHead>User Email</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Time</TableHead>
                <TableHead className="text-right pr-6">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                  </TableCell>
                </TableRow>
              ) : tickets?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                    Queue is empty.
                  </TableCell>
                </TableRow>
              ) : (
                tickets?.slice(0, 10).map((t) => (
                  <TableRow key={t.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium pl-6 font-mono text-sm">{t.id}</TableCell>
                    <TableCell>{t.user_email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-background">{t.category}</Badge>
                    </TableCell>
                    <TableCell>
                      {!t.cache_hit ? (
                        <Badge variant="secondary" className="bg-amber-100/80 text-amber-800 hover:bg-amber-100 border-amber-200 dark:bg-amber-900/50 dark:text-amber-300 dark:border-amber-800/50">
                          <Clock className="w-3 h-3 mr-1.5" />
                          Requires Review
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-green-100/80 text-green-800 hover:bg-green-100 border-green-200 dark:bg-green-900/50 dark:text-green-300 dark:border-green-800/50">
                          <CheckCircle2 className="w-3 h-3 mr-1.5" />
                          Auto-Resolved
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <Link href={`/admin/ticket/${t.id}`}>
                        <Button variant="ghost" size="sm" className="hover:bg-primary/10 hover:text-primary">
                          Review <ArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
