import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../api/settings", () => ({
  getSettings: vi.fn().mockResolvedValue({
    smtp_host: "",
    smtp_port: 587,
    smtp_username: "",
    smtp_use_tls: true,
    smtp_from_address: "",
    smtp_to_address: "",
    smtp_password_configured: false,
  }),
  updateSmtp: vi.fn().mockResolvedValue({}),
  testSmtp: vi.fn().mockResolvedValue({ success: true }),
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

import { SmtpSettingsPage } from "./SmtpSettingsPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SmtpSettingsPage />
    </QueryClientProvider>
  );
}

describe("SmtpSettingsPage", () => {
  it("renders SMTP Configuration heading", () => {
    renderPage();

    expect(screen.getByText("SMTP Configuration")).toBeInTheDocument();
  });

  it("shows Not configured when no SMTP", () => {
    renderPage();

    expect(screen.getByText("Not configured")).toBeInTheDocument();
  });

  it("renders Host and Port input fields", async () => {
    renderPage();

    expect(await screen.findByText("Host")).toBeInTheDocument();
    expect(screen.getByText("Port")).toBeInTheDocument();
  });

  it("renders Username and Password fields", async () => {
    renderPage();

    expect(await screen.findByText("Username")).toBeInTheDocument();
    expect(screen.getByText("Password")).toBeInTheDocument();
  });

  it("renders Save and Test buttons", () => {
    renderPage();

    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("renders Use TLS checkbox", () => {
    renderPage();

    expect(screen.getByText("Use TLS")).toBeInTheDocument();
  });
});
