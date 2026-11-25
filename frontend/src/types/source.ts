export interface Source {
  id: number;
  site_key: string;
  label: string;
  is_enabled: boolean;
  auth_type: string;
  auth_configured: boolean;
  auth_status: "valid" | "expired" | "unknown";
  auth_last_checked: string | null;
  sync_interval_bookmarks: string;
  sync_interval_updates: string;
  rate_limit_config: RateLimitConfig | null;
  config_configured: boolean;
  config_fields: Record<string, string> | null;
  created_at: string | null;
  updated_at: string | null;
  validation_message?: string | null;
}

export interface RateLimitConfig {
  delay_ms: number;
  max_pages: number;
}

export interface SupportedSite {
  site_key: string;
  label: string;
  auth_types: string[];
  config_fields: Record<string, string> | null;
  default_rate_limit: RateLimitConfig;
}

export interface SyncState {
  source_site: string;
  last_synced: string | null;
  last_bookmark_id: string | null;
  total_bookmarks: number;
  total_synced: number;
  sync_status: "idle" | "syncing" | "blocked" | "failed";
  sync_progress_current: number;
  sync_progress_total: number | null;
  sync_message: string | null;
}

export interface ScheduledJob {
  id: string;
  name: string;
  next_run_time: string | null;
  trigger: string;
}
