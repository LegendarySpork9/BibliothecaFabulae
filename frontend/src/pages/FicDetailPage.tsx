import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  Clock,
  ExternalLink,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useContext, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ToastContext } from "../contexts/ToastContext";
import { checkFicUpdate, deleteFic, getFic, getUpdateStatus } from "../api/fics";

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  es: "Spanish",
  fr: "French",
  de: "German",
  it: "Italian",
  pt: "Portuguese",
  ru: "Russian",
  zh: "Chinese",
  ja: "Japanese",
  ko: "Korean",
  pl: "Polish",
  nl: "Dutch",
  sv: "Swedish",
  fi: "Finnish",
  da: "Danish",
  no: "Norwegian",
  hu: "Hungarian",
  cs: "Czech",
  tr: "Turkish",
  ar: "Arabic",
  he: "Hebrew",
  hi: "Hindi",
  th: "Thai",
  vi: "Vietnamese",
  id: "Indonesian",
  uk: "Ukrainian",
  ro: "Romanian",
  el: "Greek",
  bg: "Bulgarian",
  hr: "Croatian",
  sk: "Slovak",
  sl: "Slovenian",
  lt: "Lithuanian",
  lv: "Latvian",
  et: "Estonian",
  tl: "Filipino",
  ms: "Malay",
};

function getLanguageName(code: string | null | undefined): string | null {
  if (!code) {
    return null;
  }

  return LANGUAGE_NAMES[code.toLowerCase()] || code;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  const hasTime = /T\d{2}:|\s\d{2}:/.test(value);

  const d = new Date(value);

  if (isNaN(d.getTime())) {
    return value;
  }

  return hasTime
    ? d.toLocaleDateString() + " " + d.toLocaleTimeString()
    : d.toLocaleDateString();
}

type BadgeColor = "gray" | "red" | "yellow" | "orange" | "purple" | "blue" | "pink" | "green" | "indigo" | "cyan";

const badgeStyles: Record<BadgeColor, string> = {
  gray: "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300",
  red: "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300",
  yellow: "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300",
  orange: "bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300",
  purple: "bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300",
  blue: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
  pink: "bg-pink-100 dark:bg-pink-900/40 text-pink-700 dark:text-pink-300",
  green: "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300",
  indigo: "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300",
  cyan: "bg-cyan-100 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300",
};

function Badge({ text, color }: { text: string; color: BadgeColor }) {
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded-full ${badgeStyles[color]}`}>
      {text}
    </span>
  );
}

function TagRow({ label, items, color }: { label: string; items: string[]; color: BadgeColor }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="flex gap-3 items-baseline">
      <span className="text-gray-500 dark:text-gray-400 w-32 shrink-0 text-right text-sm leading-5">
        {label}:
      </span>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <Badge key={item} text={item} color={color} />
        ))}
      </div>
    </div>
  );
}

export function FicDetailPage() {
  const { ficId } = useParams<{ ficId: string }>();
  const navigate = useNavigate();
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [checkStarted, setCheckStarted] = useState(false);
  const [serverConfirmedRunning, setServerConfirmedRunning] = useState(false);

  const { data: updateStatus } = useQuery({
    queryKey: ["update-status"],
    queryFn: getUpdateStatus,
    refetchInterval: 3000,
  });

  const isCheckRunningOnServer = updateStatus?.bulk_running ||
    updateStatus?.checking_fic_ids?.includes(Number(ficId));

  if (isCheckRunningOnServer && !serverConfirmedRunning) {
    setServerConfirmedRunning(true);
  }

  if (checkStarted && serverConfirmedRunning && !isCheckRunningOnServer) {
    setCheckStarted(false);
    setServerConfirmedRunning(false);
  }

  const isCheckBlocked = checkStarted || isCheckRunningOnServer;

  const { data: fic, isLoading, error } = useQuery({
    queryKey: ["fic", ficId],
    queryFn: () => getFic(Number(ficId)),
    enabled: !!ficId,
  });

  const updateCheckMutation = useMutation({
    mutationFn: () => checkFicUpdate(Number(ficId)),
    onMutate: () => {
      setCheckStarted(true);
      setServerConfirmedRunning(false);
    },
    onSuccess: () => {
      showToast("Update check started — you'll be notified of any changes", "success");
    },
    onError: () => {
      showToast("Failed to start update check", "error");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteFic(Number(ficId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fics"] });
      showToast("Fic removed from archive", "success");
      navigate("/library");
    },
    onError: () => {
      showToast("Failed to delete fic", "error");
    },
  });

  if (isLoading) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        Loading...
      </div>
    );
  }

  if (error || !fic) {
    return (
      <div className="text-center py-12 text-red-500">
        Failed to load fic.
      </div>
    );
  }

  const categories = fic.categories ? fic.categories.split(",").map((s) => s.trim()).filter(Boolean) : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/library"
          className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex-1">
          {fic.title}
        </h1>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-gray-600 dark:text-gray-400">
              by {fic.authors.map((a) => a.name).join(", ") || "Unknown Author"}
            </p>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              <Badge text={fic.source_site.toUpperCase()} color="gray" />
              {fic.rating && <Badge text={fic.rating} color="red" />}
              {fic.warnings && <Badge text={fic.warnings} color="orange" />}
              {fic.is_complete ? (
                <Badge text="Complete" color="green" />
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300">
                  <Clock className="h-3 w-3" /> In Progress
                </span>
              )}
              {!fic.is_source_available && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">
                  <AlertTriangle className="h-3 w-3" /> Unavailable
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => updateCheckMutation.mutate()}
              disabled={updateCheckMutation.isPending || isCheckBlocked}
              className="p-2 rounded text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
              title={isCheckBlocked ? "Update check already running" : "Check for updates"}
            >
              <RefreshCw className={`h-5 w-5 ${updateCheckMutation.isPending || isCheckBlocked ? "animate-spin" : ""}`} />
            </button>
            <a
              href={fic.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Open on source site"
            >
              <ExternalLink className="h-5 w-5" />
            </a>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="p-2 rounded text-red-400 hover:text-red-600"
              title="Delete fic"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>

        {fic.summary && (
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {fic.summary}
          </p>
        )}

        <div className="space-y-2">
          <TagRow label="Categories" items={categories} color="purple" />
          <TagRow label="Fandoms" items={fic.fandoms.map((f) => f.name)} color="cyan" />
          <TagRow label="Relationships" items={fic.relationships.map((r) => r.name)} color="pink" />
          <TagRow label="Characters" items={fic.characters.map((c) => c.name)} color="blue" />
          <TagRow label="Additional Tags" items={fic.tags.map((t) => t.name)} color="green" />
        </div>

        <div className="space-y-2 text-sm">
          <MetadataRow label="Language" value={getLanguageName(fic.language)} />
          <MetadataRow
            label="Stats"
            value={[
              fic.word_count ? `Words: ${fic.word_count.toLocaleString()}` : null,
              fic.chapter_count != null ? `Chapters: ${fic.chapter_count}` : null,
            ].filter(Boolean).join("  ·  ")}
          />

          <div className="border-t border-gray-100 dark:border-gray-700 pt-2 mt-2" />

          <MetadataRow label="Published" value={formatDateTime(fic.date_published)} />
          <MetadataRow label="Updated" value={formatDateTime(fic.date_updated)} />
          <MetadataRow label="Archived" value={formatDateTime(fic.date_archived)} />
          {fic.date_last_synced && (
            <MetadataRow label="Last Synced" value={formatDateTime(fic.date_last_synced)} />
          )}
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Chapters
          </h2>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {fic.chapters.map((chapter) => (
            <div
              key={chapter.id}
              className="px-6 py-3 flex items-center justify-between"
            >
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {chapter.title || `Chapter ${chapter.chapter_number}`}
                </span>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {chapter.word_count?.toLocaleString() || "—"} words
              </span>
            </div>
          ))}
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Delete Fic
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete &ldquo;{fic.title}&rdquo; from your archive? This will delete the stored copy from the storage location.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  deleteMutation.mutate();
                }}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetadataRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) {
    return null;
  }

  return (
    <div className="flex gap-3">
      <span className="text-gray-500 dark:text-gray-400 w-32 shrink-0 text-right">{label}:</span>
      <span className="text-gray-900 dark:text-gray-100">{value}</span>
    </div>
  );
}
