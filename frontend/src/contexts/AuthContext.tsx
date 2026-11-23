import axios from "axios";
import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import * as authApi from "../api/auth";
import { setAccessToken } from "../api/client";
import type { HealthResponse } from "../types";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  requiresSetup: boolean;
  login: (username: string, password: string) => Promise<string>;
  verifyTotp: (
    tempToken: string,
    code: string,
    rememberDevice?: boolean,
    deviceName?: string
  ) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  requiresSetup: false,
  login: async () => "",
  verifyTotp: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [requiresSetup, setRequiresSetup] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const healthResponse = await axios.get<HealthResponse>("/api/health");
        const { setup_complete } = healthResponse.data;

        if (!setup_complete) {
          setRequiresSetup(true);
          setIsLoading(false);

          return;
        }

        const tokenResponse = await authApi.refreshToken();
        setAccessToken(tokenResponse.access_token);
        setIsAuthenticated(true);
      }

      catch {
        setIsAuthenticated(false);
      }

      finally {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const response = await authApi.login(username, password);

    return response.temp_token!;
  }, []);

  const verifyTotp = useCallback(
    async (
      tempToken: string,
      code: string,
      rememberDevice = false,
      deviceName?: string
    ) => {
      const response = await authApi.verifyTotp(
        tempToken,
        code,
        rememberDevice,
        deviceName
      );
      setAccessToken(response.access_token);
      setIsAuthenticated(true);
      setRequiresSetup(false);
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    }

    finally {
      setAccessToken(null);
      setIsAuthenticated(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        requiresSetup,
        login,
        verifyTotp,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
