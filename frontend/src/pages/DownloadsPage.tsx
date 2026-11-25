import {
  AlertCircle,
  CheckCircle,
  Clock,
  Download,
  Loader2,
  Trash2,
} from "lucide-react";
import { useContext, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  clearAllDownloads,
  clearCompletedDownloads,
  getDownloads,
} from "../api/fics";
import { ToastContext } from "../contexts/ToastContext";
import type { DownloadJob } from "../types/fic";

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) {
    return "—";
  }

  const d = new Date(iso);

  return d.toLocaleDateString() + " " + d.toLocaleTimeString();
}

const statusConfig: Record<
  string,
  { icon: typeof CheckCircle; color: string; bgColor: string; label: string }
> = {
  queued: {
    icon: Clock,
    color: "text-gray-500",
    bgColor: "bg-gray-100 dark:bg-gray-700",
    label: "Queued",
  },
  downloading: {
    icon: Loader2,
    color: "text-blue-500",
    bgColor: "bg-blue-50 dark:bg-blue-900/30",
    label: "Downloading",
  },
  complete: {
    icon: CheckCircle,
    color: "text-green-500",
    bgColor: "bg-green-50 dark:bg-green-900/30",
    label: "Complete",
  },
  failed: {
    icon: AlertCircle,
    color: "text-red-500",
    bgColor: "bg-red-50 dark:bg-red-900/30",
    label: "Failed",
  },
};

const statusFilters = [
  { value: "", label: "All" },
  { value: "queued", label: "Queued" },
  { value: "downloading", label: "Downloading" },
  { value: "complete", label: "Complete" },
  { value: "failed", label: "Failed" },
];

function formatEta(seconds: number): string {
  if (seconds <= 0) {
    return "";
  }

  if (seconds < 60) {
    return `~${Math.round(seconds)}s`;
  }

  if (seconds < 3600) {
    return `~${Math.round(seconds / 60)}m`;
  }

  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);

  return `~${h}h ${m}m`;
}

function JobRow({ job, avgPerChapter }: { job: DownloadJob; avgPerChapter: Record<string, number> }) {
  const config = statusConfig[job.status] || statusConfig.queued;
  const StatusIcon = config.icon;

  let etaText = "";
  let elapsedText = "";
  const siteAvg = job.source_site ? avgPerChapter[job.source_site] : null;

  if (job.status === "downloading") {
    if (job.download_started_at) {
      const elapsed = (Date.now() - new Date(job.download_started_at).getTime()) / 1000;
      elapsedText = formatEta(elapsed);
    }

    if (job.chapter_count && siteAvg && siteAvg > 0) {
      const totalEst = job.chapter_count * siteAvg;
      const elapsed = job.download_started_at
        ? (Date.now() - new Date(job.download_started_at).getTime()) / 1000
        : 0;
      const remaining = totalEst - elapsed;
      etaText = remaining > 0 ? formatEta(remaining) : "";
    }
  } else if (job.status === "queued" && job.chapter_count && siteAvg && siteAvg > 0) {
    etaText = formatEta(job.chapter_count * siteAvg);
  }

  return (
    <div className="px-6 py-4 flex items-center gap-4">
      <div className={`p-2 rounded-lg ${config.bgColor}`}>
        <StatusIcon
          className={`h-5 w-5 ${config.color} ${job.status === "downloading" ? "animate-spin" : ""}`}
        />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {job.fic_title && job.fic_id ? (
            <Link
              to={`/library/${job.fic_id}`}
              className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline truncate"
            >
              {job.fic_title}
            </Link>
          ) : (
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {job.fic_title || job.url}
            </span>
          )}
          {job.source_site && (
            <span className="shrink-0 px-1.5 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
              {job.source_site.toUpperCase()}
            </span>
          )}
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
          {job.status_message || config.label}
        </p>
      </div>

      <div className="text-right shrink-0">
        <span
          className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${config.bgColor} ${config.color}`}
        >
          {config.label}
        </span>
        {job.status === "downloading" && (
          <div className="text-xs mt-0.5 space-y-0.5">
            {job.chapter_count && (
              <p className="text-gray-400 dark:text-gray-500">{job.chapter_count} chapters</p>
            )}
            {elapsedText && (
              <p className="text-blue-500 dark:text-blue-400">{elapsedText} elapsed</p>
            )}
            {etaText && (
              <p className="text-indigo-500 dark:text-indigo-400">{etaText} remaining</p>
            )}
          </div>
        )}
        {job.status === "queued" && etaText && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            Est. {etaText}
          </p>
        )}
        {job.status === "complete" && job.download_seconds != null && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            Took {formatEta(job.download_seconds)}{job.chapter_count ? ` · ${job.chapter_count} ch` : ""}
          </p>
        )}
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
          {formatDateTime(job.started_at)}
        </p>
      </div>
    </div>
  );
}

export function DownloadsPage() {
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [page, setPage] = useState(0);
  const [showClearAll, setShowClearAll] = useState(false);
  const [showClearCompleted, setShowClearCompleted] = useState(false);
  const pageSize = 25;

  const { data, isLoading } = useQuery({
    queryKey: ["downloads", statusFilter, sourceFilter, page],
    queryFn: () =>
      getDownloads({
        status: statusFilter || undefined,
        source_site: sourceFilter || undefined,
        limit: pageSize,
        offset: page * pageSize,
      }),
    refetchInterval: 3000,
  });

  const clearCompletedMutation = useMutation({
    mutationFn: clearCompletedDownloads,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["downloads"] });
      setShowClearCompleted(false);
      showToast(`Cleared ${result.cleared} completed downloads`, "success");
    },
  });

  const clearAllMutation = useMutation({
    mutationFn: clearAllDownloads,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["downloads"] });
      setShowClearAll(false);
      showToast(`Cleared ${result.cleared} downloads`, "success");
    },
  });

  const { data: completedData } = useQuery({
    queryKey: ["downloads", "completed-count"],
    queryFn: () => getDownloads({ status: "complete", limit: 1 }),
    refetchInterval: 5000,
  });

  const jobs = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);
  const hasCompleted = (completedData?.total || 0) > 0;

  const sourceSites = [...new Set(jobs.map((j) => j.source_site).filter(Boolean))] as string[];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Downloads
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} download{total !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-2">
          {hasCompleted && (
            <button
              onClick={() => setShowClearCompleted(true)}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              Clear Completed
            </button>
          )}
          {total > 0 && (
            <button
              onClick={() => setShowClearAll(true)}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              Clear All
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {statusFilters.map((f) => (
            <button
              key={f.value}
              onClick={() => { setStatusFilter(f.value); setPage(0); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                statusFilter === f.value
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {sourceSites.length > 1 && (
          <select
            value={sourceFilter}
            onChange={(e) => { setSourceFilter(e.target.value); setPage(0); }}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-1.5 text-xs"
          >
            <option value="">All Sites</option>
            {sourceSites.map((site) => (
              <option key={site} value={site}>
                {site.toUpperCase()}
              </option>
            ))}
          </select>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Loading...
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <Download className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {statusFilter ? `No ${statusFilter} downloads.` : "No downloads yet."}
          </p>
        </div>
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {jobs.map((job) => (
              <JobRow key={job.id} job={job} avgPerChapter={data?.avg_seconds_per_chapter || {}} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showClearCompleted && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Clear Completed Downloads
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Remove all completed download records? This only clears the history — downloaded fics are not affected.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowClearCompleted(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => clearCompletedMutation.mutate()}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Clear Completed
              </button>
            </div>
          </div>
        </div>
      )}

      {showClearAll && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Clear All Downloads
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Remove all download records including active and failed? This only clears the history — downloaded fics are not affected.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowClearAll(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => clearAllMutation.mutate()}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
