import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
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

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardPage />
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
});
