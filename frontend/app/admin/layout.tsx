"use client";

import { Ticket, LayoutDashboard, BookOpen, Settings, History, BarChart3, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard & Queue", href: "/admin", icon: LayoutDashboard },
    { name: "Issue History", href: "/admin/history", icon: History },
    { name: "Analytics & Reports", href: "#", icon: BarChart3 },
    { name: "Knowledge Base", href: "#", icon: BookOpen },
    { name: "Settings", href: "#", icon: Settings },
  ];

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/20 lg:flex-row">
      <aside className="fixed inset-y-0 left-0 z-10 hidden w-64 flex-col border-r bg-background sm:flex shadow-sm justify-between">
        <div>
          <div className="flex h-16 items-center border-b px-4 lg:px-6">
            <Link href="/admin" className="flex items-center gap-2 font-bold text-lg group">
              <div className="p-1.5 bg-primary/10 rounded-md group-hover:bg-primary/20 transition-colors">
                <Ticket className="h-5 w-5 text-primary" />
              </div>
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-600">SyncroDesk Admin</span>
            </Link>
          </div>
          <div className="flex-1 overflow-auto py-4">
            <nav className="grid items-start px-3 text-sm font-medium space-y-1.5">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all ${
                      isActive
                        ? "bg-primary/10 text-primary shadow-sm border border-primary/10"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
        
        {/* User Profile Section */}
        <div className="border-t p-4 mb-2 flex items-center justify-between">
          <div className="flex items-center gap-3 bg-muted/50 p-2.5 rounded-xl border border-border/50 hover:bg-muted transition-colors cursor-pointer group flex-1 max-w-[80%]">
            <Avatar className="h-9 w-9 border border-primary/20">
              <AvatarImage src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="@admin" />
              <AvatarFallback>AD</AvatarFallback>
            </Avatar>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium leading-none truncate">Admin User</p>
              <p className="text-xs text-muted-foreground mt-1 truncate">admin@syncrodesk.com</p>
            </div>
            <LogOut className="h-4 w-4 text-muted-foreground group-hover:text-destructive transition-colors opacity-0 group-hover:opacity-100" />
          </div>
          <ThemeToggle />
        </div>
      </aside>
      <div className="flex flex-1 flex-col sm:gap-4 sm:py-4 sm:pl-64">
        {children}
      </div>
    </div>
  );
}
