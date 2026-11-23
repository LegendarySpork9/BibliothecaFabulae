import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useState } from "react";

import { getSettings, updateStoragePath } from "../../api/settings";
import { getStorageInfo } from "../../api/storage";
import { useToast } from "../../hooks/useToast";

function formatBytes(bytes: number): string {
  if (bytes === 0) {

    return "0 B";
  }
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function StorageSettingsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const [editing, setEditing] = useState(false);
  const [newPath, setNewPath] = useState("");

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const { data: storage } = useQuery({
    queryKey: ["storage"],
    queryFn: getStorageInfo,
  });

  const mutation = useMutation({
    mutationFn: (path: string) => updateStoragePath(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["storage"] });
      setEditing(false);
      showToast("Storage path updated", "success");
    },
    onError: () => showToast("Failed to update storage path", "error"),
  });

  return (
    <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
          Current Storage Path
        </h3>
        {editing ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={() => mutation.mutate(newPath)}
              disabled={mutation.isPending}
              className="rounded-lg bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => setEditing(false)}
              className="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-600 dark:text-gray-400"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <code className="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-800 dark:text-gray-200">
              {settings?.storage_path || "Not configured"}
            </code>
            <button
              onClick={() => {
                setNewPath(settings?.storage_path || "");
                setEditing(true);
              }}
              className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Change
            </button>
          </div>
        )}
      </div>

      {storage && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            Usage Breakdown
          </h3>
          <div className="space-y-2 text-sm">
            {[
              { label: "HTML Files", bytes: storage.breakdown.fics_html },
              { label: "EPUB Files", bytes: storage.breakdown.fics_epub },
              { label: "Audio Cache", bytes: storage.breakdown.audio },
              { label: "Database", bytes: storage.breakdown.database },
              { label: "Other", bytes: storage.breakdown.other },
            ].map(({ label, bytes }) => (
              <div
                key={label}
                className="flex justify-between text-gray-600 dark:text-gray-400"
              >
                <span>{label}</span>
                <span>{formatBytes(bytes)}</span>
              </div>
            ))}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-2 flex justify-between font-medium text-gray-900 dark:text-gray-100">
              <span>Archive Storage Used</span>
              <span>{formatBytes(storage.storage_used_bytes)}</span>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2 flex justify-between text-gray-600 dark:text-gray-400">
              <span>Disk Used</span>
              <span>{formatBytes(storage.disk_used_bytes)}</span>
            </div>
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Disk Free</span>
              <span>{formatBytes(storage.disk_free_bytes)}</span>
            </div>
            <div className="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Disk Total</span>
              <span>{formatBytes(storage.disk_total_bytes)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
