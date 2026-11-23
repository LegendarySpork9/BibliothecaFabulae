import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../api/settings", () => ({
  getSettings: vi.fn().mockResolvedValue({
    storage_path: "",
  }),
  updateStoragePath: vi.fn().mockResolvedValue({}),
}));

vi.mock("../../api/storage", () => ({
  getStorageInfo: vi.fn().mockResolvedValue({
    storage_used_bytes: 0,
    disk_free_bytes: 1_000_000_000,
    disk_used_bytes: 500_000_000,
    disk_total_bytes: 1_500_000_000,
    breakdown: {
      fics_html: 0,
      fics_epub: 0,
      audio: 0,
      database: 0,
      other: 0,
    },
  }),
}));

vi.mock("../../hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

import { StorageSettingsPage } from "./StorageSettingsPage";

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <StorageSettingsPage />
    </QueryClientProvider>
  );
}

describe("StorageSettingsPage", () => {
  it("renders Current Storage Path heading", () => {
    renderPage();

    expect(screen.getByText("Current Storage Path")).toBeInTheDocument();
  });

  it("shows Not configured when no settings", () => {
    renderPage();

    expect(screen.getByText("Not configured")).toBeInTheDocument();
  });

  it("renders Change link", async () => {
    renderPage();

    expect(await screen.findByText("Change")).toBeInTheDocument();
  });

  it("renders usage breakdown section with HTML Files, EPUB Files, etc.", async () => {
    renderPage();

    expect(
      await screen.findByText("Usage Breakdown")
    ).toBeInTheDocument();
    expect(screen.getByText("HTML Files")).toBeInTheDocument();
    expect(screen.getByText("EPUB Files")).toBeInTheDocument();
    expect(screen.getByText("Audio Cache")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Other")).toBeInTheDocument();
  });
});
