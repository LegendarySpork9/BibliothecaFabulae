export interface FicSummary {
  id: number;
  source_site: string;
  source_id: string;
  title: string;
  rating: string | null;
  word_count: number | null;
  chapter_count: number | null;
  is_complete: boolean;
  is_favourite: boolean;
  is_source_available: boolean;
  import_method: string;
  date_archived: string | null;
  authors: { id: number; name: string }[];
}

export interface Fic extends FicSummary {
  source_url: string;
  summary: string | null;
  language: string | null;
  warnings: string | null;
  categories: string | null;
  reading_status: string;
  html_path: string | null;
  epub_path: string | null;
  date_published: string | null;
  date_updated: string | null;
  date_last_synced: string | null;
  fandoms: { id: number; name: string }[];
  relationships: { id: number; name: string }[];
  characters: { id: number; name: string }[];
  tags: { id: number; name: string; tag_type: string }[];
  chapters: ChapterSummary[];
}

export interface ChapterSummary {
  id: number;
  chapter_number: number;
  title: string | null;
  word_count: number | null;
}

export interface ChapterContent extends ChapterSummary {
  content: string;
}

export interface SearchResult {
  fic_id: number;
  fic_title: string;
  source_site: string;
  chapter_id: number;
  snippet: string;
}

export interface FicListResponse {
  items: FicSummary[];
  total: number;
}

export interface SearchResponse {
  items: SearchResult[];
  total: number;
}

export interface AuthHelpEntry {
  format: string;
  instructions: string;
  expiry?: string;
}

export interface SupportedSiteInfo {
  domain: string;
  name: string;
  example_urls: string[];
  manual_import: boolean;
  update_checking: boolean;
  list_sync: boolean;
  sync_type: string | null;
  sync_label: string | null;
  sync_description: string | null;
  auth_required: boolean;
  config_required: boolean;
  auth_help: Record<string, AuthHelpEntry> | null;
  config_help: Record<string, AuthHelpEntry> | null;
}

export interface DownloadJob {
  id: number;
  url: string;
  source_site: string | null;
  source_id: string | null;
  fic_title: string | null;
  status: "queued" | "downloading" | "complete" | "failed";
  status_message: string | null;
  fic_id: number | null;
  chapter_count: number | null;
  download_seconds: number | null;
  started_at: string | null;
  download_started_at: string | null;
  completed_at: string | null;
  eta_seconds: number | null;
}

export interface DownloadJobsResponse {
  items: DownloadJob[];
  total: number;
  avg_seconds_per_chapter: Record<string, number>;
}
