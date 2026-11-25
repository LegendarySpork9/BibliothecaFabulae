import type { Notification, NotificationPreference } from "../types";

import client from "./client";

interface NotificationsResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

export async function getNotifications(params?: {
  unread_only?: boolean;
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<NotificationsResponse> {
  const response = await client.get("/notifications", { params });

  return response.data;
}

export async function getUnreadCount(): Promise<{ unread_count: number }> {
  const response = await client.get("/notifications/unread-count");

  return response.data;
}

export async function markRead(id: number): Promise<void> {
  await client.patch(`/notifications/${id}/read`);
}

export async function markAllRead(): Promise<void> {
  await client.post("/notifications/mark-all-read");
}

export async function deleteNotification(id: number): Promise<void> {
  await client.delete(`/notifications/${id}`);
}

export async function getPreferences(): Promise<NotificationPreference[]> {
  const response = await client.get("/notifications/preferences");

  return response.data;
}

export async function updatePreference(
  notificationType: string,
  data: { ui_enabled?: boolean; email_enabled?: boolean }
): Promise<void> {
  await client.patch(`/notifications/preferences/${notificationType}`, data);
}
