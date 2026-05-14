"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, CheckCircle2, Ticket, Bot, UserIcon, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";

export default function UserPortal() {
  const [email, setEmail] = useState("");
  const [issue, setIssue] = useState("");

  const ticketMutation = useMutation({
    mutationFn: async (data: { user_email: string; issue_text: string }) => {
      const response = await fetch('/api/ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Failed to submit ticket');
      }
      
      return response.json();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !issue) return;
    ticketMutation.mutate({ user_email: email, issue_text: issue });
  };

  return (
    <div className="flex min-h-screen w-full flex-col lg:flex-row relative">
      {/* Top absolute area for ThemeToggle */}
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Left Section: Information & Tutorial */}
      <div className="flex-1 bg-muted/30 p-8 lg:p-16 flex flex-col justify-center relative overflow-hidden dark:bg-muted/10 border-r border-border/50">
        {/* Decorative Gradients */}
        <div className="absolute top-0 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-50 pointer-events-none" />
        <div className="absolute bottom-0 -right-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl opacity-50 pointer-events-none" />
        
        <div className="relative z-10 max-w-lg mx-auto lg:mx-0 lg:max-w-xl space-y-8">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-primary/10 rounded-xl">
                <Ticket className="w-8 h-8 text-primary" />
              </div>
              <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-600">
                SyncroDesk
              </h1>
            </div>
            <p className="text-muted-foreground text-lg font-medium leading-relaxed">
              Experience the next generation of IT support. Our AI agent instantly processes, triages, and attempts to resolve your issues before they even reach a human agent.
            </p>
          </div>

          <div className="space-y-6 pt-6 border-t border-border/50">
            <h3 className="text-xl font-semibold">How it works</h3>
            
            <div className="flex gap-4 items-start">
              <div className="bg-blue-100 dark:bg-blue-900/50 p-3 rounded-full shrink-0 shadow-sm border border-blue-200 dark:border-blue-800">
                <UserIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">1. Report Your Issue</h4>
                <p className="text-sm text-muted-foreground mt-1">Describe the problem clearly using the form on the right.</p>
              </div>
            </div>
            
            <div className="flex gap-4 items-start">
              <div className="bg-primary/10 p-3 rounded-full shrink-0 shadow-sm border border-primary/20">
                <Bot className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">2. AI Instant Triage</h4>
                <p className="text-sm text-muted-foreground mt-1">Our intelligent agent analyzes your problem and drafts an immediate solution based on internal Knowledge Base.</p>
              </div>
            </div>

            <div className="flex gap-4 items-start">
              <div className="bg-amber-100 dark:bg-amber-900/50 p-3 rounded-full shrink-0 shadow-sm border border-amber-200 dark:border-amber-800">
                <ShieldCheck className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground">3. Human Review & Resolution</h4>
                <p className="text-sm text-muted-foreground mt-1">If the AI cannot fully resolve your issue, it seamlessly forwards context-rich details to our IT Helpdesk staff.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Section: Form */}
      <div className="flex-1 bg-background p-8 lg:p-16 flex flex-col justify-center items-center relative">
        <div className="w-full max-w-md">
          {ticketMutation.isSuccess ? (
            <Card className="shadow-xl border-primary/20 bg-card/80 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="p-8 text-center space-y-6">
                <div className="flex justify-center">
                  <div className="rounded-full bg-green-500/10 p-4">
                    <CheckCircle2 className="w-16 h-16 text-green-500" />
                  </div>
                </div>
                <div className="space-y-3">
                  <h2 className="text-2xl font-bold tracking-tight">Ticket Created!</h2>
                  <p className="text-muted-foreground">
                    Ticket <strong className="text-foreground font-mono bg-muted px-2 py-1 rounded">#{ticketMutation.data?.ticket_id}</strong> has been created.
                  </p>
                  <div className="bg-muted/50 border p-5 rounded-xl mt-6 text-sm text-left shadow-sm space-y-3">
                    <div className="flex justify-between items-center pb-3 border-b border-border/50">
                      <span className="text-muted-foreground">Category</span>
                      <span className="font-semibold bg-primary/10 text-primary px-3 py-1 rounded-full text-xs">
                        {ticketMutation.data?.category}
                      </span>
                    </div>
                    <div className="flex justify-between items-center pb-3 border-b border-border/50">
                      <span className="text-muted-foreground">Status</span>
                      <span className="font-semibold text-amber-600 dark:text-amber-500">
                        Initial solution drafted
                      </span>
                    </div>
                    <p className="text-muted-foreground leading-relaxed pt-2">
                      An initial solution has been sent to <strong className="text-foreground">{email}</strong>. Our human agents will review it shortly if further action is needed.
                    </p>
                  </div>
                </div>
                <Button 
                  className="w-full mt-6 transition-all hover:scale-[1.02]" 
                  variant="outline" 
                  size="lg"
                  onClick={() => {
                    setEmail("");
                    setIssue("");
                    ticketMutation.reset();
                  }}
                >
                  Submit Another Issue
                </Button>
              </div>
            </Card>
          ) : (
            <Card className="shadow-2xl border-border/50 bg-card/95 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-300">
              <form onSubmit={handleSubmit}>
                <CardHeader className="space-y-1 pb-6">
                  <CardTitle className="text-2xl font-bold">Report an Issue</CardTitle>
                  <CardDescription className="text-base">
                    Fill out the form below to get immediate assistance.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium">Email Address</Label>
                    <Input 
                      id="email" 
                      type="email" 
                      placeholder="employee@company.com" 
                      className="h-11 transition-all focus-visible:ring-primary/50"
                      required 
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={ticketMutation.isPending}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="issue" className="text-sm font-medium">Issue Description</Label>
                    <Textarea 
                      id="issue" 
                      placeholder="E.g., My MacBook cannot connect to the corporate VPN..." 
                      className="min-h-[140px] resize-y transition-all focus-visible:ring-primary/50" 
                      required
                      value={issue}
                      onChange={(e) => setIssue(e.target.value)}
                      disabled={ticketMutation.isPending}
                    />
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Button 
                    type="submit" 
                    className="w-full h-12 text-base font-semibold transition-all hover:scale-[1.02] shadow-lg hover:shadow-primary/25" 
                    disabled={ticketMutation.isPending || !email || !issue}
                  >
                    {ticketMutation.isPending ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-3 animate-spin" />
                        Processing Ticket with AI...
                      </>
                    ) : (
                      "Submit Ticket"
                    )}
                  </Button>
                </CardFooter>
              </form>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
