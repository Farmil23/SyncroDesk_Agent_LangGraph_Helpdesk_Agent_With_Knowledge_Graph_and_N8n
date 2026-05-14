"use client";

import { useQuery } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, Filter, History, CheckCircle2, XCircle, DatabaseZap, ServerCrash, Loader2 } from "lucide-react";
import Link from "next/link";

type Ticket = {
  id: string;
  user_email: string;
  category: string;
  status: string;
  cache_hit: boolean;
  created_at: string;
};

export default function HistoryPage() {
  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets"],
    queryFn: async () => {
      const res = await fetch("/api/tickets");
      if (!res.ok) throw new Error("Failed to fetch tickets");
      const json = await res.json();
      return json.data as Ticket[];
    },
  });

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Issue History</h2>
          <p className="text-muted-foreground mt-1">View and search through past tickets and resolutions.</p>
        </div>
      </div>

      <div className="flex items-center gap-4 py-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search tickets by ID, email, or keywords..."
            className="pl-8 bg-background border-border/50 shadow-sm"
          />
        </div>
        <Button variant="outline" className="gap-2 bg-background shadow-sm border-border/50">
          <Filter className="h-4 w-4" />
          Filter
        </Button>
      </div>

      <Card className="shadow-md border-border/50">
        <CardHeader className="bg-muted/30 border-b pb-4">
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-muted-foreground" />
            Archived Tickets
          </CardTitle>
          <CardDescription>A comprehensive record of all closed and resolved support requests.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/10">
              <TableRow>
                <TableHead className="pl-6">Ticket ID</TableHead>
                <TableHead>User Email</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Cache Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right pr-6">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                  </TableCell>
                </TableRow>
              ) : tickets?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                    No tickets found.
                  </TableCell>
                </TableRow>
              ) : (
                tickets?.map((t) => (
                  <TableRow key={t.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium pl-6 font-mono text-sm text-muted-foreground">{t.id}</TableCell>
                    <TableCell>{t.user_email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-background text-muted-foreground">{t.category}</Badge>
                    </TableCell>
                    <TableCell>
                      {t.status === "Requires Review" ? (
                        <div className="flex items-center gap-2 text-amber-600">
                          <XCircle className="w-4 h-4" />
                          <span className="text-sm">Requires Review</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-green-500">
                          <CheckCircle2 className="w-4 h-4" />
                          <span className="text-sm">Resolved</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {t.cache_hit ? (
                        <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:border-blue-800/50">
                          <DatabaseZap className="w-3 h-3 mr-1" />
                          Cache Hit
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/50 dark:text-amber-300 dark:border-amber-800/50">
                          <ServerCrash className="w-3 h-3 mr-1" />
                          Cache Miss
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {new Date(t.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <Link href={`/admin/ticket/${t.id}`}>
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                          View Details
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
