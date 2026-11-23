import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../api/settings", () => ({
  getSettings: vi.fn().mockResolvedValue({
    cloudflare_trust_enabled: false,
  }),
  getAccount: vi.fn().mockResolvedValue({
    username: "admin",
  }),
  changePassword: vi.fn().mockResolvedValue({}),
  regenerateTotp: vi.fn().mockResolvedValue({}),
  confirmNewTotp: vi.fn().mockResolvedValue({}),
}));

vi.mock("../../api/auth", () => ({
  getSessions: vi.fn().mockResolvedValue([]),
  revokeSession: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../api/client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

import { AccountSettingsPage } from "./AccountSettingsPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AccountSettingsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("AccountSettingsPage", () => {
  it("renders Account heading", () => {
    renderPage();

    expect(screen.getByText("Account")).toBeInTheDocument();
  });

  it("renders Change Password heading", () => {
    renderPage();

    expect(screen.getByText("Change Password")).toBeInTheDocument();
  });

  it("renders Two-Factor Authentication heading", () => {
    renderPage();

    expect(
      screen.getByText("Two-Factor Authentication")
    ).toBeInTheDocument();
  });

  it("renders Active Sessions heading", () => {
    renderPage();

    expect(screen.getByText("Active Sessions")).toBeInTheDocument();
  });

  it("renders Cloudflare Zero Trust heading", () => {
    renderPage();

    expect(
      screen.getByText("Cloudflare Zero Trust")
    ).toBeInTheDocument();
  });

  it("renders username in Account section", async () => {
    renderPage();

    expect(await screen.findByText("admin")).toBeInTheDocument();
  });

  it("renders password input fields", () => {
    renderPage();

    expect(
      screen.getByPlaceholderText("Current password")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("New password")
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Confirm new password")
    ).toBeInTheDocument();
  });

  it("renders Update Password button", () => {
    renderPage();

    expect(screen.getByText("Update Password")).toBeInTheDocument();
  });

  it("renders Regenerate TOTP Secret button", () => {
    renderPage();

    expect(
      screen.getByText("Regenerate TOTP Secret")
    ).toBeInTheDocument();
  });
});
