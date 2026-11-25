import { Plus } from "lucide-react";
import { useContext, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AddSourceModal } from "../../components/sources/AddSourceModal";
import { EditConfigModal } from "../../components/sources/EditConfigModal";
import { EditSourceAuthModal } from "../../components/sources/EditSourceAuthModal";
import { SourceCard } from "../../components/sources/SourceCard";
import { ToastContext } from "../../contexts/ToastContext";
import {
  createSource,
  deleteSource,
  getSources,
  getSupportedSites,
  updateSource,
  updateSourceAuth,
  updateSourceConfig,
  validateSourceAuth,
} from "../../api/sources";
import type { Source } from "../../types/source";

export function SourcesSettingsPage() {
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();

  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [configuringSource, setConfiguringSource] = useState<Source | null>(null);
  const [deletingSource, setDeletingSource] = useState<Source | null>(null);
  const [validatingIds, setValidatingIds] = useState<Set<number>>(new Set());

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
    refetchInterval: 5000,
  });

  const { data: supportedSites = [] } = useQuery({
    queryKey: ["supported-sites"],
    queryFn: getSupportedSites,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      updateSource(id, { is_enabled: enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: () => {
      showToast("Failed to update source", "error");
    },
  });

  const addMutation = useMutation({
    mutationFn: (data: { site_key: string; auth_type: string; auth_data?: string; config_data?: string }) =>
      createSource(data),
    onSuccess: (result) => {
      queryClient.setQueryData<Source[]>(["sources"], (old) =>
        old ? [...old, result] : [result]
      );
      setShowAddModal(false);

      const msg = result.validation_message;

      if (!msg) {
        showToast("Source added", "success");
      } else if (result.auth_status === "valid") {
        showToast(msg, "success");
      } else if (result.auth_status === "expired") {
        showToast(`Source added — ${msg}`, "error");
      } else {
        showToast(`Source added — ${msg}`, "warning");
      }
    },
    onError: () => {
      showToast("Failed to add source", "error");
    },
  });

  const updateAuthMutation = useMutation({
    mutationFn: ({ id, auth_type, auth_data }: { id: number; auth_type: string; auth_data?: string }) =>
      updateSourceAuth(id, { auth_type, auth_data }),
    onSuccess: (result) => {
      queryClient.setQueryData<Source[]>(["sources"], (old) =>
        old?.map((s) => (s.id === result.id ? result : s))
      );
      setEditingSource(null);

      const msg = result.validation_message;

      if (result.auth_status === "valid") {
        showToast(msg || "Credentials saved and verified", "success");
      } else if (result.auth_status === "expired") {
        showToast(msg || "Credentials saved but validation failed", "error");
      } else if (msg && msg.startsWith("Format valid")) {
        showToast(msg, "success");
      } else {
        showToast(msg || "Credentials saved — could not verify right now", "warning");
      }
    },
    onError: () => {
      showToast("Failed to update authentication", "error");
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: ({ id, config_data }: { id: number; config_data: string }) =>
      updateSourceConfig(id, { config_data }),
    onSuccess: (result) => {
      queryClient.setQueryData<Source[]>(["sources"], (old) =>
        old?.map((s) => (s.id === result.id ? result : s))
      );
      setConfiguringSource(null);
      showToast("Configuration saved", "success");
    },
    onError: () => {
      showToast("Failed to save configuration", "error");
    },
  });

  const updateCronMutation = useMutation({
    mutationFn: ({ id, bookmarkCron, updateCron }: { id: number; bookmarkCron: string; updateCron: string }) =>
      updateSource(id, { sync_interval_bookmarks: bookmarkCron, sync_interval_updates: updateCron }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      showToast("Schedule updated", "success");
    },
    onError: () => {
      showToast("Failed to update schedule", "error");
    },
  });

  const validateMutation = useMutation({
    mutationFn: (id: number) => validateSourceAuth(id),
    onMutate: (id) => {
      setValidatingIds((prev) => new Set(prev).add(id));
    },
    onSuccess: (result) => {
      queryClient.setQueryData<Source[]>(["sources"], (old) =>
        old?.map((s) => (s.id === result.id ? result : s))
      );

      const msg = result.validation_message || "";

      if (result.auth_status === "valid") {
        showToast(msg || "Credentials are valid", "success");
      } else if (result.auth_status === "expired") {
        showToast(msg || "Credentials are invalid or expired", "error");
      } else {
        showToast(msg || "Could not verify credentials right now", "warning");
      }
    },
    onError: () => {
      showToast("Validation failed", "error");
    },
    onSettled: (_data, _error, id) => {
      setValidatingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);

        return next;
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      showToast("Source removed", "success");
    },
    onError: () => {
      showToast("Failed to remove source", "error");
    },
  });

  const handleDelete = (source: Source) => {
    setDeletingSource(source);
  };

  if (isLoading) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        Loading sources...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Configure source sites for downloading and syncing fanfiction.
        </p>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Source
        </button>
      </div>

      {sources.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <p className="text-gray-500 dark:text-gray-400">
            No sources configured yet. Add a source to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
          {sources.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              onToggle={(id, enabled) => toggleMutation.mutate({ id, enabled })}
              onEditAuth={setEditingSource}
              onEditConfig={setConfiguringSource}
              onDelete={handleDelete}
              onUpdateCron={(id, bookmarkCron, updateCron) =>
                updateCronMutation.mutate({ id, bookmarkCron, updateCron })
              }
              onValidate={(id) => validateMutation.mutate(id)}
              isValidating={validatingIds.has(source.id)}
            />
          ))}
        </div>
      )}

      {showAddModal && (
        <AddSourceModal
          supportedSites={supportedSites}
          existingSiteKeys={sources.map((s) => s.site_key)}
          onAdd={(siteKey, authType, authData, configData) =>
            addMutation.mutate({ site_key: siteKey, auth_type: authType, auth_data: authData, config_data: configData })
          }
          onClose={() => setShowAddModal(false)}
        />
      )}

      {editingSource && (
        <EditSourceAuthModal
          source={editingSource}
          supportedSites={supportedSites}
          onSave={(sourceId, authType, authData) =>
            updateAuthMutation.mutate({ id: sourceId, auth_type: authType, auth_data: authData })
          }
          onClose={() => setEditingSource(null)}
          isSaving={updateAuthMutation.isPending}
        />
      )}

      {configuringSource && (
        <EditConfigModal
          source={configuringSource}
          onSave={(sourceId, configData) =>
            updateConfigMutation.mutate({ id: sourceId, config_data: configData })
          }
          onClose={() => setConfiguringSource(null)}
          isSaving={updateConfigMutation.isPending}
        />
      )}

      {deletingSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Remove Source
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Remove {deletingSource.label}? This will not delete any downloaded fics.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeletingSource(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  deleteMutation.mutate(deletingSource.id);
                  setDeletingSource(null);
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
