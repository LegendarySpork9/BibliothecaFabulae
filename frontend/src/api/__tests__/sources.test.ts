import { describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import client from "../client";
import {
  createSource,
  deleteSource,
  getSource,
  getSources,
  getSupportedSites,
  updateSource,
  updateSourceAuth,
  updateSourceConfig,
  validateSourceAuth,
} from "../sources";

describe("sources API", () => {
  it("getSupportedSites calls GET /sources/supported", async () => {
    const sites = [
      { site_key: "ao3", label: "AO3", auth_types: ["cookie"] },
    ];

    vi.mocked(client.get).mockResolvedValueOnce({ data: sites });

    const result = await getSupportedSites();

    expect(client.get).toHaveBeenCalledWith("/sources/supported");
    expect(result).toEqual(sites);
  });

  it("getSources calls GET /sources", async () => {
    const sources = [
      { id: 1, site_key: "ao3", label: "AO3", is_enabled: true },
    ];

    vi.mocked(client.get).mockResolvedValueOnce({ data: sources });

    const result = await getSources();

    expect(client.get).toHaveBeenCalledWith("/sources");
    expect(result).toEqual(sources);
  });

  it("getSource calls GET /sources/:id", async () => {
    const source = { id: 1, site_key: "ao3", label: "AO3" };

    vi.mocked(client.get).mockResolvedValueOnce({ data: source });

    const result = await getSource(1);

    expect(client.get).toHaveBeenCalledWith("/sources/1");
    expect(result).toEqual(source);
  });

  it("createSource calls POST /sources with body", async () => {
    const data = {
      site_key: "ao3",
      auth_type: "cookie",
      auth_data: "session=abc123",
      sync_interval_bookmarks: "1h",
      sync_interval_updates: "6h",
    };
    const created = { id: 1, ...data, is_enabled: true };

    vi.mocked(client.post).mockResolvedValueOnce({ data: created });

    const result = await createSource(data);

    expect(client.post).toHaveBeenCalledWith("/sources", data);
    expect(result).toEqual(created);
  });

  it("updateSource calls PATCH /sources/:id with body", async () => {
    const data = { is_enabled: false, sync_interval_bookmarks: "2h" };
    const updated = { id: 1, site_key: "ao3", ...data };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: updated });

    const result = await updateSource(1, data);

    expect(client.patch).toHaveBeenCalledWith("/sources/1", data);
    expect(result).toEqual(updated);
  });

  it("updateSourceAuth calls PATCH /sources/:id/auth", async () => {
    const data = { auth_type: "cookie", auth_data: "session=new" };
    const updated = { id: 1, site_key: "ao3", auth_type: "cookie" };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: updated });

    const result = await updateSourceAuth(1, data);

    expect(client.patch).toHaveBeenCalledWith("/sources/1/auth", data);
    expect(result).toEqual(updated);
  });

  it("updateSourceConfig calls PATCH /sources/:id/config", async () => {
    const data = { config_data: '{"username":"testuser"}' };
    const updated = { id: 1, site_key: "fimfiction" };

    vi.mocked(client.patch).mockResolvedValueOnce({ data: updated });

    const result = await updateSourceConfig(1, data);

    expect(client.patch).toHaveBeenCalledWith("/sources/1/config", data);
    expect(result).toEqual(updated);
  });

  it("deleteSource calls DELETE /sources/:id", async () => {
    vi.mocked(client.delete).mockResolvedValueOnce({ data: null });

    await deleteSource(1);

    expect(client.delete).toHaveBeenCalledWith("/sources/1");
  });

  it("validateSourceAuth calls POST /sources/:id/validate", async () => {
    const validated = { id: 1, auth_status: "valid" };

    vi.mocked(client.post).mockResolvedValueOnce({ data: validated });

    const result = await validateSourceAuth(1);

    expect(client.post).toHaveBeenCalledWith("/sources/1/validate");
    expect(result).toEqual(validated);
  });
});
