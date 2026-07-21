import axios from "axios";

import { logger } from "./logger";

function getApiBaseURL(): string {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050";
  }
  const { hostname } = window.location;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8050";
  }
  return `https://${hostname.replace("zsc-sac.", "zsc-sac-api.")}`;
}

const api = axios.create({
  baseURL: getApiBaseURL(),
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  logger.debug("API request", {
    method: config.method?.toUpperCase() ?? "GET",
    url: config.url ?? "",
  });
  return config;
});

api.interceptors.response.use(
  (response) => {
    logger.debug("API response", {
      method: response.config.method?.toUpperCase() ?? "GET",
      url: response.config.url ?? "",
      status: response.status,
    });
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url ?? "";

    if (status === 401) {
      logger.warn("API 401 — clearing token and redirecting to login", { url });
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    } else {
      logger.error("API error", {
        method: error.config?.method?.toUpperCase() ?? "GET",
        url,
        status: status ?? "network",
        message: error.message,
      });
    }

    return Promise.reject(error);
  },
);

export default api;
