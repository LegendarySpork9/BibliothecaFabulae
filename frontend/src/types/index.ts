export interface User {
  username: string;
  created_at: string;
  totp_enabled: boolean;
}

export interface AppSettings {
  storage_path: string;
  theme: "dark" | "light";
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_password_configured: boolean;
  smtp_use_tls: boolean;
  smtp_from_address: string | null;
  smtp_to_address: string | null;
  backup_location: string | null;
  backup_schedule: string | null;
  cloudflare_trust_enabled: boolean;
  remember_device_days: number;
  setup_complete: boolean;
}

export type NotificationType =
  | "fic_updated"
  | "sync_complete"
  | "sync_failed"
  | "auth_required"
  | "storage_low"
  | "fic_unavailable"
  | "scanner_new_works"
  | "audio_ready";

export type Severity = "info" | "warning" | "error" | "success";

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  message: string;
  severity: Severity;
  is_read: boolean;
  related_fic_id: number | null;
  email_sent: boolean;
  created_at: string;
}

export interface NotificationPreference {
  notification_type: NotificationType;
  ui_enabled: boolean;
  email_enabled: boolean;
}

export interface Session {
  id: number;
  device_name: string | null;
  is_current: boolean;
  remember_device: boolean;
  created_at: string | null;
  last_used_at: string | null;
  expires_at: string;
}

export interface StorageInfo {
  disk_total_bytes: number;
  disk_used_bytes: number;
  disk_free_bytes: number;
  storage_used_bytes: number;
  breakdown: {
    fics_html: number;
    fics_epub: number;
    audio: number;
    database: number;
    other: number;
  };
}

export interface StorageWarning {
  warning: string;
  message: string;
  free_bytes: number;
  threshold_percent: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  setup_complete: boolean;
}
