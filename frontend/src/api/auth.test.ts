import { describe, expect, it, vi } from "vitest";

vi.mock("./client", () => ({
  default: { post: vi.fn(), get: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

import client from "./client";
import {
  getSessions,
  login,
  logout,
  refreshToken,
  verifyTotp,
} from "./auth";

describe("auth API", () => {
  it("login calls POST /auth/login", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { requires_totp: true, temp_token: "tok123" },
    });

    const result = await login("admin", "pass");

    expect(client.post).toHaveBeenCalledWith("/auth/login", {
      username: "admin",
      password: "pass",
    });
    expect(result).toEqual({
      requires_totp: true,
      temp_token: "tok123",
    });
  });

  it("verifyTotp calls POST /auth/verify-totp", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { access_token: "abc", token_type: "bearer" },
    });

    const result = await verifyTotp("tok123", "123456", true, "My PC");

    expect(client.post).toHaveBeenCalledWith("/auth/verify-totp", {
      temp_token: "tok123",
      totp_code: "123456",
      remember_device: true,
      device_name: "My PC",
    });
    expect(result).toEqual({
      access_token: "abc",
      token_type: "bearer",
    });
  });

  it("logout calls POST /auth/logout", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({ data: null });

    await logout();

    expect(client.post).toHaveBeenCalledWith("/auth/logout");
  });

  it("getSessions calls GET /auth/sessions", async () => {
    const sessions = [{ id: 1, device_name: "Chrome" }];

    vi.mocked(client.get).mockResolvedValueOnce({ data: sessions });

    const result = await getSessions();

    expect(client.get).toHaveBeenCalledWith("/auth/sessions");
    expect(result).toEqual(sessions);
  });

  it("refreshToken calls POST /auth/refresh", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { access_token: "new-tok", token_type: "bearer" },
    });

    const result = await refreshToken();

    expect(client.post).toHaveBeenCalledWith("/auth/refresh");
    expect(result).toEqual({
      access_token: "new-tok",
      token_type: "bearer",
    });
  });
});
