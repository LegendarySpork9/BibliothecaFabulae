import { describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

import client from "../client";
import {
  clearAllDownloads,
  clearCompletedDownloads,
  checkAllFicUpdates,
  checkFicUpdate,
  deleteFic,
  getChapterContent,
  getChapters,
  getDownloads,
  getFic,
  getFics,
  getSupportedSites,
  getUpdateStatus,
  importFic,
  searchFicContent,
} from "../fics";

describe("fics API", () => {
  it("getFics calls GET /fics with no params", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0 },
    });

    const result = await getFics();

    expect(client.get).toHaveBeenCalledWith("/fics", { params: undefined });
    expect(result).toEqual({ items: [], total: 0 });
  });

  it("getFics calls GET /fics with filter params", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0 },
    });

    const params = {
      source_site: "ao3",
      is_complete: true,
      sort: "title",
      limit: 10,
      offset: 0,
    };

    await getFics(params);

    expect(client.get).toHaveBeenCalledWith("/fics", { params });
  });

  it("getFic calls GET /fics/:id", async () => {
    const mockFic = { id: 42, title: "Test Fic" };

    vi.mocked(client.get).mockResolvedValueOnce({ data: mockFic });

    const result = await getFic(42);

    expect(client.get).toHaveBeenCalledWith("/fics/42");
    expect(result).toEqual(mockFic);
  });

  it("getChapters calls GET /fics/:ficId/chapters", async () => {
    const chapters = [{ id: 1, chapter_number: 1, title: "Ch1", word_count: 500 }];

    vi.mocked(client.get).mockResolvedValueOnce({ data: chapters });

    const result = await getChapters(42);

    expect(client.get).toHaveBeenCalledWith("/fics/42/chapters");
    expect(result).toEqual(chapters);
  });

  it("getChapterContent calls GET /fics/:ficId/chapters/:chapterId", async () => {
    const chapter = { id: 7, chapter_number: 1, title: "Ch1", word_count: 500, content: "<p>text</p>" };

    vi.mocked(client.get).mockResolvedValueOnce({ data: chapter });

    const result = await getChapterContent(42, 7);

    expect(client.get).toHaveBeenCalledWith("/fics/42/chapters/7");
    expect(result).toEqual(chapter);
  });

  it("importFic calls POST /fics/import with url", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { status: "queued", message: "Download started" },
    });

    const result = await importFic("https://archiveofourown.org/works/12345");

    expect(client.post).toHaveBeenCalledWith("/fics/import", {
      url: "https://archiveofourown.org/works/12345",
    });
    expect(result).toEqual({ status: "queued", message: "Download started" });
  });

  it("deleteFic calls DELETE /fics/:id", async () => {
    vi.mocked(client.delete).mockResolvedValueOnce({ data: null });

    await deleteFic(42);

    expect(client.delete).toHaveBeenCalledWith("/fics/42");
  });

  it("getSupportedSites calls GET /fics/sites", async () => {
    const sites = [{ domain: "archiveofourown.org", name: "AO3" }];

    vi.mocked(client.get).mockResolvedValueOnce({ data: sites });

    const result = await getSupportedSites();

    expect(client.get).toHaveBeenCalledWith("/fics/sites");
    expect(result).toEqual(sites);
  });

  it("getDownloads calls GET /fics/downloads with no params", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0, avg_seconds_per_chapter: {} },
    });

    const result = await getDownloads();

    expect(client.get).toHaveBeenCalledWith("/fics/downloads", {
      params: undefined,
    });
    expect(result).toEqual({ items: [], total: 0, avg_seconds_per_chapter: {} });
  });

  it("getDownloads calls GET /fics/downloads with filter params", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0, avg_seconds_per_chapter: {} },
    });

    const params = { status: "complete", limit: 10, offset: 0 };

    await getDownloads(params);

    expect(client.get).toHaveBeenCalledWith("/fics/downloads", { params });
  });

  it("clearCompletedDownloads calls DELETE /fics/downloads/completed", async () => {
    vi.mocked(client.delete).mockResolvedValueOnce({
      data: { cleared: 5 },
    });

    const result = await clearCompletedDownloads();

    expect(client.delete).toHaveBeenCalledWith("/fics/downloads/completed");
    expect(result).toEqual({ cleared: 5 });
  });

  it("clearAllDownloads calls DELETE /fics/downloads", async () => {
    vi.mocked(client.delete).mockResolvedValueOnce({
      data: { cleared: 12 },
    });

    const result = await clearAllDownloads();

    expect(client.delete).toHaveBeenCalledWith("/fics/downloads");
    expect(result).toEqual({ cleared: 12 });
  });

  it("getUpdateStatus calls GET /fics/update-status", async () => {
    const status = { bulk_running: false, checking_fic_ids: [] };

    vi.mocked(client.get).mockResolvedValueOnce({ data: status });

    const result = await getUpdateStatus();

    expect(client.get).toHaveBeenCalledWith("/fics/update-status");
    expect(result).toEqual(status);
  });

  it("checkFicUpdate calls POST /fics/:ficId/check-update", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { status: "started", message: "Checking for updates" },
    });

    const result = await checkFicUpdate(42);

    expect(client.post).toHaveBeenCalledWith("/fics/42/check-update");
    expect(result).toEqual({ status: "started", message: "Checking for updates" });
  });

  it("checkAllFicUpdates calls POST /fics/check-updates", async () => {
    vi.mocked(client.post).mockResolvedValueOnce({
      data: { status: "started", message: "Bulk update check started" },
    });

    const result = await checkAllFicUpdates();

    expect(client.post).toHaveBeenCalledWith("/fics/check-updates");
    expect(result).toEqual({ status: "started", message: "Bulk update check started" });
  });

  it("searchFicContent calls GET /fics/search/content with params", async () => {
    vi.mocked(client.get).mockResolvedValueOnce({
      data: { items: [], total: 0 },
    });

    const params = { q: "dragon", limit: 20, offset: 0 };

    const result = await searchFicContent(params);

    expect(client.get).toHaveBeenCalledWith("/fics/search/content", { params });
    expect(result).toEqual({ items: [], total: 0 });
  });
});
