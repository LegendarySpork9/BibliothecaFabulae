import type { Source, SupportedSite } from "../types/source";

import client from "./client";

export async function getSupportedSites(): Promise<SupportedSite[]> {
  const response = await client.get("/sources/supported");

  return response.data;
}

export async function getSources(): Promise<Source[]> {
  const response = await client.get("/sources");

  return response.data;
}

export async function getSource(id: number): Promise<Source> {
  const response = await client.get(`/sources/${id}`);

  return response.data;
}

export async function createSource(data: {
  site_key: string;
  auth_type?: string;
  auth_data?: string;
  sync_interval_bookmarks?: string;
  sync_interval_updates?: string;
  rate_limit_config?: { delay_ms: number; max_pages: number };
}): Promise<Source> {
  const response = await client.post("/sources", data);

  return response.data;
}

export async function updateSource(
  id: number,
  data: {
    is_enabled?: boolean;
    sync_interval_bookmarks?: string;
    sync_interval_updates?: string;
    rate_limit_config?: { delay_ms: number; max_pages: number };
  }
): Promise<Source> {
  const response = await client.patch(`/sources/${id}`, data);

  return response.data;
}

export async function updateSourceAuth(
  id: number,
  data: { auth_type: string; auth_data?: string }
): Promise<Source> {
  const response = await client.patch(`/sources/${id}/auth`, data);

  return response.data;
}

export async function updateSourceConfig(
  id: number,
  data: { config_data: string }
): Promise<Source> {
  const response = await client.patch(`/sources/${id}/config`, data);

  return response.data;
}

export async function deleteSource(id: number): Promise<void> {
  await client.delete(`/sources/${id}`);
}

export async function validateSourceAuth(id: number): Promise<Source> {
  const response = await client.post(`/sources/${id}/validate`);

  return response.data;
}
