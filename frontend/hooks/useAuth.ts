"use client";

import { useCallback, useState } from "react";
import api from "@/lib/api";
import type { TokenResponse, UserResponse } from "@/types";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  loading: boolean;
}

function getInitialAuthState(): AuthState {
  if (typeof window === "undefined") {
    return { user: null, token: null, loading: false };
  }
  const token = localStorage.getItem("token");
  const email = localStorage.getItem("user_email");
  const role = localStorage.getItem("user_role");
  if (token && email && role) {
    return { user: { email, role }, token, loading: false };
  }
  return { user: null, token: null, loading: false };
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(getInitialAuthState);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<TokenResponse>("/api/v1/auth/login", {
      email,
      password,
    });

    localStorage.setItem("token", data.access_token);

    const me = await api.get<UserResponse>("/api/v1/auth/me");
    localStorage.setItem("user_email", me.data.email);
    localStorage.setItem("user_role", me.data.role);

    setState({
      user: me.data,
      token: data.access_token,
      loading: false,
    });

    return me.data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_role");
    setState({ user: null, token: null, loading: false });
    window.location.href = "/login";
  }, []);

  return {
    user: state.user,
    token: state.token,
    loading: state.loading,
    isAuthenticated: !!state.token,
    login,
    logout,
  };
}
