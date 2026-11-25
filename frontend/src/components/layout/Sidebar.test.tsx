import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    requiresSetup: false,
    login: vi.fn(),
    verifyTotp: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("../../api/notifications", () => ({
  getUnreadCount: vi.fn().mockResolvedValue({ unread_count: 0 }),
}));

import { Sidebar } from "./Sidebar";

function renderSidebar(overrides?: Partial<{
  open: boolean;
  collapsed: boolean;
}>) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Sidebar
          open={overrides?.open ?? true}
          collapsed={overrides?.collapsed ?? false}
          onClose={vi.fn()}
          onToggleCollapse={vi.fn()}
        />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Sidebar", () => {
  it("renders Bibliotheca Fabulae title", () => {
    renderSidebar();

    expect(
      screen.getAllByText("Bibliotheca Fabulae").length
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders Dashboard nav link", () => {
    renderSidebar();

    expect(
      screen.getAllByText("Dashboard").length
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders Notifications nav link", () => {
    renderSidebar();

    expect(
      screen.getAllByText("Notifications").length
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders Logout button", () => {
    renderSidebar();

    expect(
      screen.getAllByText("Logout").length
    ).toBeGreaterThanOrEqual(1);
  });
});
