import type { StorageInfo, StorageWarning } from "../types";

import client from "./client";

export async function getStorageInfo(): Promise<StorageInfo> {
  const response = await client.get("/storage");

  return response.data;
}

export async function getStorageWarnings(): Promise<StorageWarning[]> {
  const response = await client.get("/storage/warnings");

  return response.data;
}
