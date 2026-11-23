import { describe, expect, it, vi } from "vitest";

vi.mock("./client", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

import client from "./client";
import {
  deleteNotification,
  getNotifications,
  getUnreadCount,
  markAllRead,
  markRead,
} from "./notifications";

describe("notifications API", () => {
  it("getNotifications calls GET /notifications", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0, unread_count: 0 },
    });

    const result = await getNotifications();

    expect(client.get).toHaveBeenCalledWith("/notifications", {
      params: undefined,
    });
    expect(result).toEqual({ items: [], total: 0, unread_count: 0 });
  });

  it("getUnreadCount calls GET /notifications/unread-count", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { count: 5 },
    });

    const result = await getUnreadCount();

    expect(client.get).toHaveBeenCalledWith("/notifications/unread-count");
    expect(result).toEqual({ count: 5 });
  });

  it("markRead calls PATCH /notifications/{id}/read", async () => {
    vi.mocked(client.patch).mockResolvedValueOnce({ data: undefined });

    await markRead(42);

    expect(client.patch).toHaveBeenCalledWith("/notifications/42/read");
  });

  it("markAllRead calls POST /notifications/mark-all-read", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({ data: undefined });

    await markAllRead();

    expect(client.post).toHaveBeenCalledWith(
      "/notifications/mark-all-read"
    );
  });

  it("deleteNotification calls DELETE /notifications/{id}", async () => {
    vi.mocked(client.delete).mockResolvedValueOnce({ data: undefined });

    await deleteNotification(7);

    expect(client.delete).toHaveBeenCalledWith("/notifications/7");
  });
});
