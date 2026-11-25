import type {
  ChapterContent,
  ChapterSummary,
  DownloadJobsResponse,
  Fic,
  FicListResponse,
  SearchResponse,
  SupportedSiteInfo,
} from "../types/fic";

import client from "./client";

export async function getFics(params?: {
  source_site?: string;
  is_complete?: boolean;
  is_favourite?: boolean;
  is_source_available?: boolean;
  import_method?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}): Promise<FicListResponse> {
  const response = await client.get("/fics", { params });

  return response.data;
}

export async function getFic(id: number): Promise<Fic> {
  const response = await client.get(`/fics/${id}`);

  return response.data;
}

export async function getChapters(ficId: number): Promise<ChapterSummary[]> {
  const response = await client.get(`/fics/${ficId}/chapters`);

  return response.data;
}

export async function getChapterContent(
  ficId: number,
  chapterId: number
): Promise<ChapterContent> {
  const response = await client.get(`/fics/${ficId}/chapters/${chapterId}`);

  return response.data;
}

export async function deleteFic(id: number): Promise<void> {
  await client.delete(`/fics/${id}`);
}

export async function importFic(
  url: string
): Promise<{ status: string; message: string }> {
  const response = await client.post("/fics/import", { url });

  return response.data;
}

export async function getSupportedSites(): Promise<SupportedSiteInfo[]> {
  const response = await client.get("/fics/sites");

  return response.data;
}

export async function getDownloads(params?: {
  status?: string;
  source_site?: string;
  limit?: number;
  offset?: number;
}): Promise<DownloadJobsResponse> {
  const response = await client.get("/fics/downloads", { params });

  return response.data;
}

export async function clearCompletedDownloads(): Promise<{ cleared: number }> {
  const response = await client.delete("/fics/downloads/completed");

  return response.data;
}

export async function clearAllDownloads(): Promise<{ cleared: number }> {
  const response = await client.delete("/fics/downloads");

  return response.data;
}

export async function getUpdateStatus(): Promise<{
  bulk_running: boolean;
  checking_fic_ids: number[];
}> {
  const response = await client.get("/fics/update-status");

  return response.data;
}

export async function checkFicUpdate(
  ficId: number
): Promise<{ status: string; message: string }> {
  const response = await client.post(`/fics/${ficId}/check-update`);

  return response.data;
}

export async function checkAllFicUpdates(): Promise<{
  status: string;
  message: string;
}> {
  const response = await client.post("/fics/check-updates");

  return response.data;
}

export async function searchFicContent(params: {
  q: string;
  limit?: number;
  offset?: number;
}): Promise<SearchResponse> {
  const response = await client.get("/fics/search/content", { params });

  return response.data;
}
