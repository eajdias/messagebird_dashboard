/**
 * Structured logger for the frontend.
 *
 * In development, outputs coloured human-readable lines to the browser console.
 * In production (Docker standalone), console.* is preserved so docker logs captures them.
 *
 * Usage:
 *   import { logger } from "@/lib/logger";
 *   logger.info("Dashboard loaded", { conversations: 42 });
 *   logger.error("API call failed", { url, status });
 */

type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

const ENV = process.env.NODE_ENV ?? "development";
const MIN_LEVEL: LogLevel =
  (process.env.NEXT_PUBLIC_LOG_LEVEL as LogLevel) || (ENV === "production" ? "info" : "debug");

function emit(level: LogLevel, message: string, data?: Record<string, unknown>) {
  if (LEVEL_PRIORITY[level] < LEVEL_PRIORITY[MIN_LEVEL]) return;

  const ts = new Date().toISOString();
  const prefix = `[${ts}] ${level.toUpperCase().padEnd(5)}`;

  const args: unknown[] = data ? [`${prefix} ${message}`, data] : [`${prefix} ${message}`];

  switch (level) {
    case "debug":
      console.debug(...args);
      break;
    case "info":
      console.info(...args);
      break;
    case "warn":
      console.warn(...args);
      break;
    case "error":
      console.error(...args);
      break;
  }
}

export const logger = {
  debug: (msg: string, data?: Record<string, unknown>) => emit("debug", msg, data),
  info: (msg: string, data?: Record<string, unknown>) => emit("info", msg, data),
  warn: (msg: string, data?: Record<string, unknown>) => emit("warn", msg, data),
  error: (msg: string, data?: Record<string, unknown>) => emit("error", msg, data),
};
