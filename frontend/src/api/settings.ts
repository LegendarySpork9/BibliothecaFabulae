import type { AppSettings, User } from "../types";

import client from "./client";

export async function getSettings(): Promise<AppSettings> {
  const response = await client.get("/settings");

  return response.data;
}

export async function updateStoragePath(storagePath: string) {
  const response = await client.patch("/settings/storage", {
    storage_path: storagePath,
  });

  return response.data;
}

export async function updateTheme(theme: "dark" | "light") {
  const response = await client.patch("/settings/theme", { theme });

  return response.data;
}

export async function updateSmtp(data: {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  smtp_from_address: string;
  smtp_to_address: string;
}) {
  const response = await client.patch("/settings/smtp", data);

  return response.data;
}

export async function testSmtp() {
  const response = await client.post("/settings/smtp/test");

  return response.data;
}

export async function updateBackup(data: {
  backup_location: string;
  backup_schedule: string;
}) {
  const response = await client.patch("/settings/backup", data);

  return response.data;
}

export async function updateRememberDevice(days: number) {
  const response = await client.patch("/settings/remember-device", { days });

  return response.data;
}

export async function getAccount(): Promise<User> {
  const response = await client.get("/account");

  return response.data;
}

export async function changePassword(data: {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}) {
  const response = await client.patch("/account/password", data);

  return response.data;
}

export async function regenerateTotp() {
  const response = await client.post("/account/totp/regenerate");

  return response.data;
}

export async function confirmNewTotp(totpCode: string, pendingSecret: string) {
  const response = await client.post("/account/totp/confirm", {
    totp_code: totpCode,
    pending_secret: pendingSecret,
  });

  return response.data;
}
