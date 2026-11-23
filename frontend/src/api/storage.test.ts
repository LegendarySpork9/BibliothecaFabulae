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
import { getStorageInfo, getStorageWarnings } from "./storage";

describe("storage API", () => {
  it("getStorageInfo calls GET /storage", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { storage_used_bytes: 1024, disk_free_bytes: 999 },
    });

    const result = await getStorageInfo();

    expect(client.get).toHaveBeenCalledWith("/storage");
    expect(result).toEqual({
      storage_used_bytes: 1024,
      disk_free_bytes: 999,
    });
  });

  it("getStorageWarnings calls GET /storage/warnings", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: [{ message: "Low disk space" }],
    });

    const result = await getStorageWarnings();

    expect(client.get).toHaveBeenCalledWith("/storage/warnings");
    expect(result).toEqual([{ message: "Low disk space" }]);
  });
});
