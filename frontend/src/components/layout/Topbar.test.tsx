import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ThemeContext } from "../../contexts/ThemeContext";

import { Topbar } from "./Topbar";

vi.mock("../../api/notifications", () => ({
  getUnreadCount: vi.fn().mockResolvedValue({ count: 0 }),
}));

function renderTopbar() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeContext.Provider
        value={{
          theme: "dark",
          setTheme: vi.fn(),
          toggleTheme: vi.fn(),
        }}
      >
        <MemoryRouter>
          <Topbar onMenuClick={vi.fn()} />
        </MemoryRouter>
      </ThemeContext.Provider>
    </QueryClientProvider>
  );
}

describe("Topbar", () => {
  it("renders the theme toggle button", () => {
    renderTopbar();

    expect(
      screen.getByTitle("Switch to light mode")
    ).toBeInTheDocument();
  });

  it("renders the notification bell", () => {
    renderTopbar();

    expect(screen.getByTitle("Notifications")).toBeInTheDocument();
  });
});
