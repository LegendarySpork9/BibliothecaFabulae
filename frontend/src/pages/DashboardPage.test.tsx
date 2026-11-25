import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DashboardPage } from "./DashboardPage";

vi.mock("../api/notifications", () => ({
  getNotifications: vi.fn().mockResolvedValue({
    items: [],
    total: 0,
    unread_count: 0,
  }),
}));

vi.mock("../api/storage", () => ({
  getStorageInfo: vi.fn().mockResolvedValue({
    storage_used_bytes: 0,
    disk_free_bytes: 1_000_000_000,
  }),
  getStorageWarnings: vi.fn().mockResolvedValue([]),
}));

vi.mock("../api/fics", () => ({
  getFics: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  importFic: vi.fn(),
}));

vi.mock("../api/sources", () => ({
  getSources: vi.fn().mockResolvedValue([]),
}));

vi.mock("../contexts/ToastContext", () => ({
  ToastContext: {
    _currentValue: { showToast: vi.fn() },
  },
}));

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("DashboardPage", () => {
  it("renders the dashboard heading", () => {
    renderDashboard();

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("shows the Bibliotheca Fabulae welcome card", () => {
    renderDashboard();

    expect(
      screen.getByText("Bibliotheca Fabulae")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Latin: Library of Tales")
    ).toBeInTheDocument();
  });

  it("renders storage card with Storage heading", async () => {
    renderDashboard();

    expect(await screen.findByText("Storage")).toBeInTheDocument();
  });

  it("renders Recent Notifications heading", () => {
    renderDashboard();

    expect(
      screen.getByText("Recent Notifications")
    ).toBeInTheDocument();
  });

  it("shows No notifications yet. when empty", async () => {
    renderDashboard();

    expect(
      await screen.findByText("No notifications yet.")
    ).toBeInTheDocument();
  });

  it("renders the description text about the archive", () => {
    renderDashboard();

    expect(
      screen.getByText(/Your self-hosted personal fanfiction archive/)
    ).toBeInTheDocument();
  });
});
