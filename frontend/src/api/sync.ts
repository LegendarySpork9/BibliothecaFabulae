import type { ScheduledJob, SyncState } from "../types/source";

import client from "./client";

export async function cancelSync(
  sourceId: number
): Promise<{ status: string; message: string }> {
  const response = await client.post(`/sources/${sourceId}/cancel-sync`);

  return response.data;
}

export async function triggerSync(
  sourceId: number
): Promise<{ status: string; message: string }> {
  const response = await client.post(`/sources/${sourceId}/sync`);

  return response.data;
}

export async function getSyncState(sourceId: number): Promise<SyncState> {
  const response = await client.get(`/sources/${sourceId}/sync-state`);

  return response.data;
}

export async function getScheduledJobs(): Promise<ScheduledJob[]> {
  const response = await client.get("/sources/scheduler/jobs");

  return response.data;
}
