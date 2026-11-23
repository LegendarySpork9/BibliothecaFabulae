import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../api/settings", () => ({
  getSettings: vi.fn().mockResolvedValue({
    backup_location: "",
    backup_schedule: "",
  }),
  updateBackup: vi.fn().mockResolvedValue({}),
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

import { BackupSettingsPage } from "./BackupSettingsPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BackupSettingsPage />
    </QueryClientProvider>
  );
}

describe("BackupSettingsPage", () => {
  it("renders Backup Configuration heading", () => {
    renderPage();

    expect(screen.getByText("Backup Configuration")).toBeInTheDocument();
  });

  it("renders backup location input", () => {
    renderPage();

    expect(screen.getByText("Backup Location")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("/path/to/backups")
    ).toBeInTheDocument();
  });

  it("renders schedule select", () => {
    renderPage();

    expect(screen.getByText("Schedule")).toBeInTheDocument();
    expect(screen.getByText("Select schedule")).toBeInTheDocument();
  });

  it("shows coming in a future update note", () => {
    renderPage();

    expect(
      screen.getByText(/coming in a future update/)
    ).toBeInTheDocument();
  });
});
