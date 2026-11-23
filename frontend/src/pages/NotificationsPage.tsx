import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Check, CheckCheck, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  deleteNotification,
  getNotifications,
  markAllRead,
  markRead,
} from "../api/notifications";
import type { NotificationType } from "../types";

const TYPE_LABELS: Record<NotificationType, string> = {
  fic_updated: "Fic Updated",
  sync_complete: "Sync Complete",
  sync_failed: "Sync Failed",
  auth_required: "Auth Required",
  storage_low: "Storage Low",
  fic_unavailable: "Fic Unavailable",
  scanner_new_works: "New Works",
  audio_ready: "Audio Ready",
};

export function NotificationsPage() {
  const queryClient = useQueryClient();

  const [unreadOnly, setUnreadOnly] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [page, setPage] = useState(0);

  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", { unreadOnly, typeFilter, page }],
    queryFn: () =>
      getNotifications({
        unread_only: unreadOnly,
        type: typeFilter || undefined,
        limit,
        offset: page * limit,
      }),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  const markReadMutation = useMutation({ mutationFn: markRead, onSuccess: invalidate });
  const markAllMutation = useMutation({ mutationFn: markAllRead, onSuccess: invalidate });
  const deleteMutation = useMutation({ mutationFn: deleteNotification, onSuccess: invalidate });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Notifications
        </h1>
        <button
          onClick={() => markAllMutation.mutate()}
          className="flex items-center gap-1 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <CheckCheck className="h-4 w-4" />
          Mark all read
        </button>
      </div>

      <div className="flex gap-3 flex-wrap">
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => {
              setUnreadOnly(e.target.checked);
              setPage(0);
            }}
            className="rounded border-gray-300 dark:border-gray-600"
          />
          Unread only
        </label>
        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300"
        >
          <option value="">All types</option>
          {Object.entries(TYPE_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="text-center text-gray-400 py-8">Loading...</div>
      ) : data?.items.length === 0 ? (
        <div className="text-center text-gray-400 py-8">No notifications.</div>
      ) : (
        <div className="space-y-2">
          {data?.items.map((n) => (
            <div
              key={n.id}
              className={`flex items-start gap-3 rounded-lg border p-4 ${
                n.is_read
                  ? "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
                  : "border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-900/20"
              }`}
            >
              <span
                className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${
                  n.is_read ? "bg-gray-300 dark:bg-gray-600" : "bg-indigo-500"
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {n.title}
                  </span>
                  <span className="text-xs text-gray-400 shrink-0">
                    {new Date(n.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {n.message}
                </p>
              </div>
              <div className="flex gap-1 shrink-0">
                {!n.is_read && (
                  <button
                    onClick={() => markReadMutation.mutate(n.id)}
                    className="p-1.5 rounded text-gray-400 hover:text-indigo-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="Mark as read"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                )}
                <button
                  onClick={() => deleteMutation.mutate(n.id)}
                  className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {data && data.total > limit && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1.5 text-sm text-gray-500">
            Page {page + 1} of {Math.ceil(data.total / limit)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= data.total}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
