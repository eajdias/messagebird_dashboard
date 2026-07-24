"use client";

import { useEffect, useCallback, useRef } from "react";

export type ShortcutHandler = () => void;

export interface Shortcut {
  keys: string[];
  handler: ShortcutHandler;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const buffer = useRef<string[]>([]);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const shortcutsRef = useRef(shortcuts);

  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
      return;
    }

    const currentShortcuts = shortcutsRef.current;

    for (const shortcut of currentShortcuts) {
      const hasMod = shortcut.keys.some((k) => k === "meta" || k === "ctrl");
      const allMatch = shortcut.keys.every((key) => {
        const lower = key.toLowerCase();
        if (lower === "meta") return e.metaKey;
        if (lower === "ctrl") return e.ctrlKey;
        if (lower === "shift") return e.shiftKey;
        if (lower === "alt") return e.altKey;
        if (hasMod) return e.key.toLowerCase() === lower;
        return e.key.toLowerCase() === lower;
      });

      if (allMatch) {
        if (hasMod) {
          e.preventDefault();
          shortcut.handler();
          return;
        }
      }
    }

    const key = e.key.toLowerCase();
    if (key === "g" && !e.metaKey && !e.ctrlKey) {
      buffer.current = ["g"];
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        buffer.current = [];
      }, 500);
      return;
    }

    if (buffer.current.length === 1 && buffer.current[0] === "g") {
      clearTimeout(timeoutRef.current);
      buffer.current = [];
      for (const shortcut of currentShortcuts) {
        if (shortcut.keys.length === 2 && shortcut.keys[0] === "g" && shortcut.keys[1] === key) {
          e.preventDefault();
          shortcut.handler();
          return;
        }
      }
    }

    buffer.current = [];
  }, []);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timeoutRef.current);
    };
  }, [handleKeyDown]);
}
