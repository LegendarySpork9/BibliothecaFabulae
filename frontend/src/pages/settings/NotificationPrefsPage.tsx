import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { getPreferences, updatePreference } from "../../api/notifications";
import { getSettings } from "../../api/settings";
import type { NotificationType } from "../../types";

const TYPE_INFO: Record<NotificationType, { label: string; description: string }> = {
  fic_updated: { label: "Fic Updated", description: "When a fic in your archive has new chapters" },
  sync_complete: { label: "Sync Complete", description: "When a bookmark sync finishes successfully" },
  sync_failed: { label: "Sync Failed", description: "When a bookmark sync encounters errors" },
  auth_required: { label: "Auth Required", description: "When a source site needs re-authentication" },
  storage_low: { label: "Storage Low", description: "When storage usage approaches the limit" },
  fic_unavailable: { label: "Fic Unavailable", description: "When a fic has been deleted or privated" },
  scanner_new_works: { label: "New Works Found", description: "When the scanner discovers new fics" },
  audio_ready: { label: "Audio Ready", description: "When TTS audio generation is complete" },
};

export function NotificationPrefsPage() {
  const queryClient = useQueryClient();

  const { data: prefs } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: getPreferences,
  });

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const smtpConfigured = settings?.smtp_password_configured ?? false;

  const mutation = useMutation({
    mutationFn: ({
      type,
      data,
    }: {
      type: string;
      data: { ui_enabled?: boolean; email_enabled?: boolean };
    }) => updatePreference(type, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] }),
  });

  return (
    <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
            <th className="px-4 py-3 text-left font-medium text-gray-500 dark:text-gray-400">
              Type
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-500 dark:text-gray-400 w-20">
              UI
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-500 dark:text-gray-400 w-20">
              Email
            </th>
          </tr>
        </thead>
        <tbody>
          {prefs?.map((pref) => {
            const info =
              TYPE_INFO[pref.notification_type as NotificationType] || {
                label: pref.notification_type,
                description: "",
              };

            return (
              <tr
                key={pref.notification_type}
                className="border-b border-gray-100 dark:border-gray-700/50"
              >
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {info.label}
                  </p>
                  <p className="text-xs text-gray-400">{info.description}</p>
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    checked={pref.ui_enabled}
                    onChange={(e) =>
                      mutation.mutate({
                        type: pref.notification_type,
                        data: { ui_enabled: e.target.checked },
                      })
                    }
                    className="rounded border-gray-300 dark:border-gray-600"
                  />
                </td>
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    checked={pref.email_enabled}
                    disabled={!smtpConfigured}
                    onChange={(e) =>
                      mutation.mutate({
                        type: pref.notification_type,
                        data: { email_enabled: e.target.checked },
                      })
                    }
                    className="rounded border-gray-300 dark:border-gray-600 disabled:opacity-50"
                    title={
                      smtpConfigured ? undefined : "Configure SMTP first"
                    }
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {!smtpConfigured && (
        <div className="px-4 py-3 text-xs text-gray-400 border-t border-gray-200 dark:border-gray-700">
          Email toggles are disabled because SMTP is not configured.
        </div>
      )}
    </div>
  );
}
