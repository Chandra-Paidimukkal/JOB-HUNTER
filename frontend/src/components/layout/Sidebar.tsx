"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/utils/cn";
import {
  LayoutDashboard, Search, Star, Zap, FileText, FileEdit,
  Bot, Mail, Building2, Linkedin, Send, MessageSquare,
  Bell, BarChart3, User, Settings, ChevronLeft, ChevronRight,
  Briefcase, TrendingUp, LogOut, Sparkles,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const NAV_ITEMS = [
  {
    group: "Main",
    items: [
      { href: "/overview", label: "Overview", icon: LayoutDashboard },
      { href: "/discover-jobs", label: "Discover Jobs", icon: Search },
      { href: "/recommended-jobs", label: "Recommended", icon: Star },
      { href: "/ai-matching", label: "AI Job Matching", icon: Zap, badge: "AI" },
    ],
  },
  {
    group: "Applications",
    items: [
      { href: "/applications", label: "My Applications", icon: Briefcase },
      { href: "/resume-manager", label: "Resume Manager", icon: FileText },
      { href: "/ai-assistant", label: "AI Application Assistant", icon: Bot, badge: "AI" },
    ],
  },
  {
    group: "Outreach",
    items: [
      { href: "/outreach-studio", label: "AI Outreach Studio", icon: Sparkles, badge: "AI" },
      { href: "/company-intelligence", label: "Company Intelligence", icon: Building2 },
      { href: "/linkedin-outreach", label: "LinkedIn Outreach", icon: Linkedin },
      { href: "/email-campaigns", label: "Email Campaigns", icon: Send },
    ],
  },
  {
    group: "Tools",
    items: [
      { href: "/interview-prep", label: "Interview Prep", icon: MessageSquare, badge: "AI" },
      { href: "/notifications", label: "Notifications", icon: Bell },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    group: "Account",
    items: [
      { href: "/profile", label: "Profile & Preferences", icon: User },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const initials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "JH";

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-card border-r border-border transition-all duration-300 relative z-30",
        collapsed ? "w-16" : "w-[260px]"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "flex items-center h-16 px-4 border-b border-border shrink-0",
        collapsed ? "justify-center" : "justify-between"
      )}>
        {!collapsed && (
          <Link href="/overview" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm text-foreground">JobHunter</span>
              <span className="text-xs text-primary font-semibold block -mt-1">AI</span>
            </div>
          </Link>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className={cn("shrink-0", collapsed && "mx-auto")}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin py-4 px-2">
        {NAV_ITEMS.map((group) => (
          <div key={group.group} className="mb-4">
            {!collapsed && (
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-1">
                {group.group}
              </p>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === `/${item.href.replace(/^\//, "")}` || 
                               pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors mb-0.5 group relative",
                    isActive
                      ? "bg-primary text-primary-foreground font-medium"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && (
                    <>
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <Badge
                          variant={isActive ? "secondary" : "default"}
                          className="text-[10px] px-1.5 py-0 h-4"
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </>
                  )}
                  {collapsed && item.badge && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-primary" />
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className={cn(
        "border-t border-border p-3 shrink-0",
        collapsed ? "flex justify-center" : ""
      )}>
        {collapsed ? (
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.avatar_url} />
            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
          </Avatar>
        ) : (
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarImage src={user?.avatar_url} />
              <AvatarFallback className="text-xs">{initials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="shrink-0 h-7 w-7"
              title="Logout"
            >
              <LogOut className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}
