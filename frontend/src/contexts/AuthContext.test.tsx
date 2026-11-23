import { render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import { useContext } from "react";
import { describe, expect, it, vi } from "vitest";

vi.mock("axios", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { setup_complete: true } }),
  },
}));

vi.mock("../api/auth", () => ({
  login: vi.fn().mockResolvedValue({
    requires_totp: true,
    temp_token: "tok123",
  }),
  refreshToken: vi.fn().mockRejectedValue(new Error("no session")),
  verifyTotp: vi.fn().mockResolvedValue({
    access_token: "abc",
    token_type: "bearer",
  }),
  logout: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
  setAccessToken: vi.fn(),
}));

import * as authApi from "../api/auth";

import { AuthContext, AuthProvider } from "./AuthContext";

function AuthConsumer() {
  const { isAuthenticated, isLoading, requiresSetup, login } =
    useContext(AuthContext);

  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="setup">{String(requiresSetup)}</span>
      <button onClick={() => login("admin", "pass")}>Login</button>
    </div>
  );
}

describe("AuthContext", () => {
  it("provides isLoading initially", () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("sets requiresSetup to true when setup_complete is false", async () => {
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { setup_complete: false },
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });

    expect(screen.getByTestId("setup").textContent).toBe("true");
  });

  it("login calls the auth API and returns temp_token", async () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });

    const result = await (authApi.login as ReturnType<typeof vi.fn>)(
      "admin",
      "pass"
    );

    expect(authApi.login).toHaveBeenCalledWith("admin", "pass");
    expect(result.temp_token).toBe("tok123");
  });
});
