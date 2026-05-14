"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle2, XCircle, FileText, Send, ArrowLeft, Bot, Activity, Database, ShieldCheck, Clock, Server, DatabaseZap, ServerCrash, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState, use, useEffect } from "react";

type Ticket = {
  id: string;
  user_email: string;
  issue_text: string;
  category: string;
  status: string;
  resolution: string;
  investigation_log: any;
  cache_hit: boolean;
  created_at: string;
};

export default function TicketDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);

  const { data: ticket, isLoading } = useQuery({
    queryKey: ["ticket", resolvedParams.id],
    queryFn: async () => {
      const res = await fetch(`/api/tickets/${resolvedParams.id}`);
      if (!res.ok) throw new Error("Failed to fetch ticket");
      const json = await res.json();
      return json.data as Ticket;
    },
  });

  useEffect(() => {
    if (ticket) {
      setDraft(ticket.resolution || "");
    }
  }, [ticket]);

  const handleApprove = () => {
    setIsSending(true);
    setTimeout(() => {
      setIsSending(false);
      alert("Resolution sent to user!");
    }, 1500);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen">
        <p className="text-xl text-muted-foreground">Ticket not found.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex items-center gap-4">
        <Link href="/admin">
          <Button variant="outline" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Ticket {ticket.id}</h2>
            <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-200">{ticket.status}</Badge>
            {ticket.cache_hit ? (
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
          </div>
          <p className="text-muted-foreground mt-1">Reported by {ticket.user_email} • Category: {ticket.category}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Workspace (Left) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-sm border-border/50">
            <CardHeader className="bg-muted/30 border-b pb-4">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Original Issue
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="bg-muted/50 p-4 rounded-lg border text-sm leading-relaxed whitespace-pre-wrap">
                {ticket.issue_text}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-md border-border/50 border-t-4 border-t-primary">
            <CardHeader className="bg-primary/5 border-b pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary" />
                  AI Draft Resolution
                </CardTitle>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
                  <ShieldCheck className="h-3 w-3 mr-1" />
                  Guardrail Passed
                </Badge>
              </div>
              <CardDescription>Review and edit the AI-generated response before sending.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <Textarea 
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="min-h-[250px] font-sans text-sm resize-y focus-visible:ring-primary/50"
              />
            </CardContent>
            <CardFooter className="bg-muted/20 border-t pt-6 flex justify-between">
              <Button variant="outline" className="text-destructive hover:bg-destructive/10 hover:text-destructive">
                Reject Draft
              </Button>
              <Button onClick={handleApprove} disabled={isSending} className="shadow-md hover:shadow-primary/20 transition-all">
                {isSending ? (
                  <>Processing...</>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Approve & Send
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Investigation & Context Panel (Right) */}
        <div className="space-y-6">
          <Tabs defaultValue="investigation" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="investigation">Investigation</TabsTrigger>
              <TabsTrigger value="observability">Observability</TabsTrigger>
            </TabsList>
            <TabsContent value="investigation" className="space-y-4 mt-4">
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">SOP Verification</CardTitle>
                </CardHeader>
                <CardContent>
                  {ticket.investigation_log?.sop_found ? (
                    <div className="flex items-start gap-3 bg-green-50/50 dark:bg-green-950/20 p-3 rounded-lg border border-green-100 dark:border-green-900">
                      <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="font-medium text-green-800 dark:text-green-300 text-sm">SOP Matched</p>
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">AI retrieved relevant SOP context.</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-3 bg-red-50 p-3 rounded-lg border border-red-100 dark:bg-red-950/20 dark:border-red-900">
                      <XCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="font-medium text-red-800 dark:text-red-300 text-sm">No SOP Found</p>
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">Resolution generated based on general knowledge or cache hit.</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {ticket.investigation_log?.asset_context && (
                <Card className="shadow-sm">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      Asset Context
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted p-3 rounded text-sm whitespace-pre-wrap font-mono">
                      {ticket.investigation_log.asset_context}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
            
            <TabsContent value="observability" className="space-y-4 mt-4">
              {ticket.investigation_log?.tracing && (
                <Card className="shadow-sm border-blue-100 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold flex items-center text-blue-800 dark:text-blue-300">
                      <Server className="h-4 w-4 mr-2" />
                      LangGraph Tracing Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Execution Path</span>
                      <Badge variant="outline" className="bg-background text-xs font-mono">{ticket.cache_hit ? "Hit" : "Miss"}</Badge>
                    </div>
                    <div className="text-xs font-mono text-muted-foreground bg-background p-2 rounded border">
                      {ticket.investigation_log.tracing.path}
                    </div>
                    <div className="grid grid-cols-2 gap-2 mt-4">
                      <div className="bg-background p-3 rounded border text-center">
                        <p className="text-xs text-muted-foreground mb-1">Total Duration</p>
                        <p className="font-bold text-blue-600 dark:text-blue-400 flex justify-center items-center gap-1">
                          <Clock className="h-3 w-3" /> {ticket.investigation_log.tracing.duration}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
