import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useState } from "react";

import { getSettings, updateBackup } from "../../api/settings";
import { useToast } from "../../hooks/useToast";

export function BackupSettingsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [location, setLocation] = useState(settings?.backup_location || "");
  const [schedule, setSchedule] = useState(settings?.backup_schedule || "");

  const mutation = useMutation({
    mutationFn: () =>
      updateBackup({ backup_location: location, backup_schedule: schedule }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      showToast("Backup settings updated", "success");
    },
    onError: () => showToast("Failed to update backup settings", "error"),
  });

  return (
    <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        Backup Configuration
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Configure where backups are stored and how often they run.
        Backups will be a zip of the database and fic files (audio excluded).
        Backup execution is not yet available — coming in a future update.
      </p>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Backup Location
        </label>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="/path/to/backups"
          className="w-full max-w-md rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Schedule
        </label>
        <select
          value={schedule}
          onChange={(e) => setSchedule(e.target.value)}
          className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-300"
        >
          <option value="">Select schedule</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
      </div>

      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        Save
      </button>
    </div>
  );
}
