import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getPreferences } from "../../api/notifications";

vi.mock("../../api/notifications", () => ({
  getPreferences: vi.fn().mockResolvedValue([]),
  updatePreference: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../api/settings", () => ({
  getSettings: vi.fn().mockResolvedValue({
    smtp_password_configured: false,
  }),
}));

import { NotificationPrefsPage } from "./NotificationPrefsPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <NotificationPrefsPage />
    </QueryClientProvider>
  );
}

describe("NotificationPrefsPage", () => {
  it("renders table headers", () => {
    renderPage();

    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("UI")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("shows SMTP not configured message", () => {
    renderPage();

    expect(
      screen.getByText(
        "Email toggles are disabled because SMTP is not configured."
      )
    ).toBeInTheDocument();
  });

  it("renders all 8 notification type labels", async () => {
    vi.mocked(getPreferences).mockResolvedValue([
      { notification_type: "fic_updated", ui_enabled: true, email_enabled: false },
      { notification_type: "sync_complete", ui_enabled: true, email_enabled: false },
      { notification_type: "sync_failed", ui_enabled: true, email_enabled: false },
      { notification_type: "auth_required", ui_enabled: true, email_enabled: false },
      { notification_type: "storage_low", ui_enabled: true, email_enabled: false },
      { notification_type: "fic_unavailable", ui_enabled: true, email_enabled: false },
      { notification_type: "scanner_new_works", ui_enabled: true, email_enabled: false },
      { notification_type: "audio_ready", ui_enabled: true, email_enabled: false },
    ]);

    renderPage();

    expect(await screen.findByText("Fic Updated")).toBeInTheDocument();
    expect(screen.getByText("Sync Complete")).toBeInTheDocument();
    expect(screen.getByText("Sync Failed")).toBeInTheDocument();
    expect(screen.getByText("Auth Required")).toBeInTheDocument();
    expect(screen.getByText("Storage Low")).toBeInTheDocument();
    expect(screen.getByText("Fic Unavailable")).toBeInTheDocument();
    expect(screen.getByText("New Works Found")).toBeInTheDocument();
    expect(screen.getByText("Audio Ready")).toBeInTheDocument();
  });
});
