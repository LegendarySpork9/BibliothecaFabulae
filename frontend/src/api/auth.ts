import client from "./client";

export interface LoginResponse {
  requires_totp: boolean;
  temp_token: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await client.post("/auth/login", { username, password });

  return response.data;
}

export async function verifyTotp(
  tempToken: string,
  totpCode: string,
  rememberDevice: boolean = false,
  deviceName?: string
): Promise<TokenResponse> {
  const response = await client.post("/auth/verify-totp", {
    temp_token: tempToken,
    totp_code: totpCode,
    remember_device: rememberDevice,
    device_name: deviceName,
  });

  return response.data;
}

export async function refreshToken(): Promise<TokenResponse> {
  const response = await client.post("/auth/refresh");

  return response.data;
}

export async function logout(): Promise<void> {
  await client.post("/auth/logout");
}

export async function getSessions() {
  const response = await client.get("/auth/sessions");

  return response.data;
}

export async function revokeSession(sessionId: number): Promise<void> {
  await client.delete(`/auth/sessions/${sessionId}`);
}
