import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
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
  getUnreadCount: vi.fn().mockResolvedValue({ count: 0 }),
}));

import { AppLayout } from "./AppLayout";

function renderLayout() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("AppLayout", () => {
  it("renders without crashing", () => {
    const { container } = renderLayout();

    expect(container.firstChild).toBeInTheDocument();
  });
});
