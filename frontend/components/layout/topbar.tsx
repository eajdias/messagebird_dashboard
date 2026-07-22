"use client";

import { useState } from "react";
import { useTheme } from "next-themes";
import { Search, Moon, Sun, LogOut, User, Command, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { CommandPalette } from "@/components/layout/command-palette";
import { MobileNav } from "@/components/layout/mobile-nav";

export function TopBar() {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-white/5 bg-card/60 px-4 backdrop-blur-xl backdrop-saturate-180 md:px-6">
      <div className="flex items-center gap-3 lg:hidden">
        <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(true)} aria-label="Abrir menu">
          <Menu className="h-5 w-5" />
        </Button>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-chart-4 text-primary-foreground text-sm font-bold">
          MB
        </div>
        <span className="bg-gradient-to-r from-primary to-chart-4 bg-clip-text text-lg font-semibold text-transparent">
          MBird
        </span>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-1 md:gap-2">
        <Button
          variant="outline"
          size="sm"
          className="hidden h-9 w-48 justify-between border-white/10 bg-white/5 text-muted-foreground backdrop-blur-sm transition-colors hover:bg-white/10 md:flex lg:w-64"
          onClick={() => {
            const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
            document.dispatchEvent(event);
          }}
        >
          <span className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            <span className="hidden lg:inline">Buscar páginas e ações...</span>
            <span className="lg:hidden">Buscar...</span>
          </span>
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <Command className="h-3 w-3" />
            K
          </kbd>
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => {
            const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
            document.dispatchEvent(event);
          }}
          aria-label="Buscar"
        >
          <Search className="h-4 w-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Alternar tema"
          className="transition-transform hover:rotate-12"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        {user && (
          <Badge variant="outline" className="hidden border-white/10 bg-white/5 text-muted-foreground sm:flex">
            <User className="mr-1 h-3 w-3" />
            <span className="hidden md:inline">{user.email}</span>
          </Badge>
        )}

        <Button variant="ghost" size="icon" onClick={logout} aria-label="Sair">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>

      <CommandPalette />
      <MobileNav open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
    </header>
  );
}
