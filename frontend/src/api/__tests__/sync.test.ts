import { describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

import client from "../client";
import {
  cancelSync,
  getScheduledJobs,
  getSyncState,
  triggerSync,
} from "../sync";

describe("sync API", () => {
  it("cancelSync calls POST /sources/:sourceId/cancel-sync", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { status: "cancelled", message: "Sync cancelled" },
    });

    const result = await cancelSync(3);

    expect(client.post).toHaveBeenCalledWith("/sources/3/cancel-sync");
    expect(result).toEqual({ status: "cancelled", message: "Sync cancelled" });
  });

  it("triggerSync calls POST /sources/:sourceId/sync", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { status: "started", message: "Sync started" },
    });

    const result = await triggerSync(5);

    expect(client.post).toHaveBeenCalledWith("/sources/5/sync");
    expect(result).toEqual({ status: "started", message: "Sync started" });
  });

  it("getSyncState calls GET /sources/:sourceId/sync-state", async () => {
    const state = {
      source_site: "ao3",
      last_synced: "2024-01-01T00:00:00Z",
      last_bookmark_id: null,
      total_bookmarks: 100,
      total_synced: 50,
      sync_status: "idle",
      sync_progress_current: 0,
      sync_progress_total: null,
      sync_message: null,
    };

    vi.mocked(client.get).mockResolvedValueOnce({ data: state });

    const result = await getSyncState(3);

    expect(client.get).toHaveBeenCalledWith("/sources/3/sync-state");
    expect(result).toEqual(state);
  });

  it("getScheduledJobs calls GET /sources/scheduler/jobs", async () => {
    const jobs = [
      {
        id: "job-1",
        name: "ao3-bookmark-sync",
        next_run_time: "2024-01-01T12:00:00Z",
        trigger: "interval[1:00:00]",
      },
    ];

    vi.mocked(client.get).mockResolvedValueOnce({ data: jobs });

    const result = await getScheduledJobs();

    expect(client.get).toHaveBeenCalledWith("/sources/scheduler/jobs");
    expect(result).toEqual(jobs);
  });
});
