import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "../contexts/AuthContext";
import { ToastContext } from "../contexts/ToastContext";

import { LoginPage } from "./LoginPage";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: { cloudflare_trust: false },
    }),
    post: vi.fn(),
  },
  setAccessToken: vi.fn(),
}));

function renderLogin(authOverrides: {
  isAuthenticated?: boolean;
  requiresSetup?: boolean;
  login?: ReturnType<typeof vi.fn>;
}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const authValue = {
    isAuthenticated: false,
    isLoading: false,
    requiresSetup: false,
    login: vi.fn(),
    verifyTotp: vi.fn(),
    logout: vi.fn(),
    ...authOverrides,
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>
        <ToastContext.Provider value={{ showToast: vi.fn() }}>
          <MemoryRouter>
            <LoginPage />
          </MemoryRouter>
        </ToastContext.Provider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe("LoginPage", () => {
  it("renders sign-in heading", async () => {
    renderLogin({});

    expect(
      await screen.findByText("Sign in to your library")
    ).toBeInTheDocument();
  });

  it("renders username and password fields", async () => {
    renderLogin({});

    await screen.findByText("Sign in to your library");

    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByText("Password")).toBeInTheDocument();
  });

  it("renders Bibliotheca Fabulae title", async () => {
    renderLogin({});

    expect(
      await screen.findByText("Bibliotheca Fabulae")
    ).toBeInTheDocument();
  });

  it("redirects to /setup when requiresSetup is true", () => {
    renderLogin({ requiresSetup: true });

    expect(
      screen.queryByText("Sign in to your library")
    ).not.toBeInTheDocument();
  });

  it("redirects to /dashboard when authenticated", () => {
    renderLogin({ isAuthenticated: true });

    expect(
      screen.queryByText("Sign in to your library")
    ).not.toBeInTheDocument();
  });

  it("renders TOTP form with Verify button after login", async () => {
    const loginMock = vi.fn().mockResolvedValue("temp-token-123");

    renderLogin({ login: loginMock });

    await screen.findByText("Sign in to your library");

    const user = userEvent.setup();
    await user.type(screen.getByRole("textbox"), "admin");
    await user.type(document.querySelector("input[type='password']")!, "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Verify")).toBeInTheDocument();
  });

  it("renders Back to login button in totp step", async () => {
    const loginMock = vi.fn().mockResolvedValue("temp-token-123");

    renderLogin({ login: loginMock });

    await screen.findByText("Sign in to your library");

    const user = userEvent.setup();
    await user.type(screen.getByRole("textbox"), "admin");
    await user.type(document.querySelector("input[type='password']")!, "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Back to login")).toBeInTheDocument();
  });

  it("renders Remember this device checkbox in totp step", async () => {
    const loginMock = vi.fn().mockResolvedValue("temp-token-123");

    renderLogin({ login: loginMock });

    await screen.findByText("Sign in to your library");

    const user = userEvent.setup();
    await user.type(screen.getByRole("textbox"), "admin");
    await user.type(document.querySelector("input[type='password']")!, "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByText("Remember this device")
    ).toBeInTheDocument();
  });
});
