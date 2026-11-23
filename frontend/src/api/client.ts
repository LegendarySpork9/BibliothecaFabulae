import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const client = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    if (
      error.response?.status === 401 &&
      !originalRequest.url?.includes("/auth/refresh") &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/verify-totp")
    ) {
      if (!refreshPromise) {
        refreshPromise = attemptRefresh();
      }

      const newToken = await refreshPromise;
      refreshPromise = null;

      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;

        return client(originalRequest);
      }

      accessToken = null;
      window.location.href = "/login";

      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

async function attemptRefresh(): Promise<string | null> {
  try {
    const response = await client.post("/auth/refresh");
    const token = response.data.access_token;
    accessToken = token;

    return token;
  }

  catch {
    return null;
  }
}

export default client;
