import { describe, expect, it, vi } from "vitest";

vi.mock("./client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

import client from "./client";
import {
  changePassword,
  confirmNewTotp,
  getAccount,
  getSettings,
  regenerateTotp,
  testSmtp,
  updateBackup,
  updateRememberDevice,
  updateSmtp,
  updateStoragePath,
  updateTheme,
} from "./settings";

describe("settings API", () => {
  it("getSettings calls GET /settings", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({ data: { storage_path: "/data" } });

    const result = await getSettings();

    expect(client.get).toHaveBeenCalledWith("/settings");
    expect(result).toEqual({ storage_path: "/data" });
  });

  it("updateTheme calls PATCH /settings/theme", async () => {
    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await updateTheme("dark");

    expect(client.patch).toHaveBeenCalledWith("/settings/theme", {
      theme: "dark",
    });
    expect(result).toEqual({ ok: true });
  });

  it("getAccount calls GET /account", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { username: "admin" },
    });

    const result = await getAccount();

    expect(client.get).toHaveBeenCalledWith("/account");
    expect(result).toEqual({ username: "admin" });
  });

  it("changePassword calls PATCH /account/password", async () => {
    const payload = {
      current_password: "old",
      new_password: "new123",
      new_password_confirm: "new123",
    };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await changePassword(payload);

    expect(client.patch).toHaveBeenCalledWith("/account/password", payload);
    expect(result).toEqual({ ok: true });
  });

  it("updateSmtp calls PATCH /settings/smtp", async () => {
    const payload = {
      smtp_host: "smtp.example.com",
      smtp_port: 587,
      smtp_username: "user",
      smtp_password: "pass",
      smtp_use_tls: true,
      smtp_from_address: "from@example.com",
      smtp_to_address: "to@example.com",
    };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await updateSmtp(payload);

    expect(client.patch).toHaveBeenCalledWith("/settings/smtp", payload);
    expect(result).toEqual({ ok: true });
  });

  it("updateBackup calls PATCH /settings/backup", async () => {
    const payload = {
      backup_location: "/backups",
      backup_schedule: "0 2 * * *",
    };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await updateBackup(payload);

    expect(client.patch).toHaveBeenCalledWith("/settings/backup", payload);
    expect(result).toEqual({ ok: true });
  });

  it("updateRememberDevice calls PATCH /settings/remember-device", async () => {
    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await updateRememberDevice(30);

    expect(client.patch).toHaveBeenCalledWith("/settings/remember-device", {
      days: 30,
    });
    expect(result).toEqual({ ok: true });
  });

  it("regenerateTotp calls POST /account/totp/regenerate", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { qr_code_base64: "abc", pending_secret: "XYZ" },
    });

    const result = await regenerateTotp();

    expect(client.post).toHaveBeenCalledWith("/account/totp/regenerate");
    expect(result).toEqual({ qr_code_base64: "abc", pending_secret: "XYZ" });
  });

  it("confirmNewTotp calls POST /account/totp/confirm", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({ data: { ok: true } });

    const result = await confirmNewTotp("123456", "PENDING_SECRET");

    expect(client.post).toHaveBeenCalledWith("/account/totp/confirm", {
      totp_code: "123456",
      pending_secret: "PENDING_SECRET",
    });
    expect(result).toEqual({ ok: true });
  });

  it("updateStoragePath calls PATCH /settings/storage", async () => {
    vi.mocked(client.patch).mockResolvedValueOnce({ data: { ok: true } });

    const result = await updateStoragePath("/new/path");

    expect(client.patch).toHaveBeenCalledWith("/settings/storage", {
      storage_path: "/new/path",
    });
    expect(result).toEqual({ ok: true });
  });

  it("testSmtp calls POST /settings/smtp/test", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { success: true },
    });

    const result = await testSmtp();

    expect(client.post).toHaveBeenCalledWith("/settings/smtp/test");
    expect(result).toEqual({ success: true });
  });
});
