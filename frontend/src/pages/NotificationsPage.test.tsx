import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NotificationsPage } from "./NotificationsPage";

import { getNotifications } from "../api/notifications";

vi.mock("../api/notifications", () => ({
  getNotifications: vi.fn().mockResolvedValue({
    items: [],
    total: 0,
    unread_count: 0,
  }),
  markAllRead: vi.fn().mockResolvedValue(undefined),
  markRead: vi.fn().mockResolvedValue(undefined),
  deleteNotification: vi.fn().mockResolvedValue(undefined),
}));

function renderNotifications() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NotificationsPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("NotificationsPage", () => {
  beforeEach(() => {
    vi.mocked(getNotifications).mockResolvedValue({
      items: [],
      total: 0,
      unread_count: 0,
    });
  });

  it("renders Notifications heading", () => {
    renderNotifications();

    expect(screen.getByText("Notifications")).toBeInTheDocument();
  });

  it("renders Mark all read button", () => {
    renderNotifications();

    expect(screen.getByText("Mark all read")).toBeInTheDocument();
  });

  it("shows No notifications when data is empty", async () => {
    renderNotifications();

    expect(
      await screen.findByText("No notifications.")
    ).toBeInTheDocument();
  });

  it("renders notification items when data is provided", async () => {
    vi.mocked(getNotifications).mockResolvedValue({
      items: [
        {
          id: 1,
          type: "fic_updated",
          title: "Chapter Released",
          message: "A new chapter is available",
          severity: "info",
          is_read: false,
          created_at: "2024-01-01T00:00:00",
        },
      ],
      total: 1,
      unread_count: 1,
    });

    renderNotifications();

    expect(await screen.findByText("Chapter Released")).toBeInTheDocument();
    expect(screen.getByText("A new chapter is available")).toBeInTheDocument();
  });

  it("renders unread indicator dot for unread notifications", async () => {
    vi.mocked(getNotifications).mockResolvedValue({
      items: [
        {
          id: 1,
          type: "fic_updated",
          title: "Unread Notice",
          message: "Test message",
          severity: "info",
          is_read: false,
          created_at: "2024-01-01T00:00:00",
        },
      ],
      total: 1,
      unread_count: 1,
    });

    renderNotifications();

    await screen.findByText("Unread Notice");

    const dot = document.querySelector(".bg-indigo-500.rounded-full");
    expect(dot).toBeInTheDocument();
  });

  it("renders Unread only checkbox", () => {
    renderNotifications();

    expect(screen.getByText("Unread only")).toBeInTheDocument();
  });

  it("renders type filter dropdown", () => {
    renderNotifications();

    expect(screen.getByText("All types")).toBeInTheDocument();
  });
});
