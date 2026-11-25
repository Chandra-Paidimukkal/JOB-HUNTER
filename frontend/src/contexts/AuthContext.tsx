"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import Cookies from "js-cookie";
import { useRouter } from "next/navigation";
import { authApi, extractApiError } from "@/services/api";
import type { User } from "@/types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    try {
      const token = Cookies.get("access_token");
      if (!token) {
        setUser(null);
        return;
      }
      const res = await authApi.me();
      setUser(res.data);
    } catch {
      setUser(null);
      Cookies.remove("access_token");
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    const { access_token, user: userData } = res.data;
    Cookies.set("access_token", access_token, { expires: 7, secure: true });
    setUser(userData);
    if (!userData.onboarding_completed) {
      router.push("/onboarding");
    } else {
      router.push("/overview");
    }
  };

  const register = async (
    email: string,
    password: string,
    fullName: string
  ) => {
    const res = await authApi.register({ email, password, full_name: fullName });
    const { access_token, user: userData } = res.data;
    Cookies.set("access_token", access_token, { expires: 7, secure: true });
    setUser(userData);
    router.push("/onboarding");
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      Cookies.remove("access_token");
      setUser(null);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
