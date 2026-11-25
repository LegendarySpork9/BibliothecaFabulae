import { useContext, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { SyncStatusCard } from "../../components/sources/SyncStatusCard";
import { ToastContext } from "../../contexts/ToastContext";
import { getSources } from "../../api/sources";
import { cancelSync, getSyncState, triggerSync } from "../../api/sync";
import type { SyncState } from "../../types/source";

export function SyncSettingsPage() {
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();
  const [syncingIds, setSyncingIds] = useState<Set<number>>(new Set());
  const [cancellingIds, setCancellingIds] = useState<Set<number>>(new Set());

  const { data: sources = [] } = useQuery({
    queryKey: ["sources"],
    queryFn: getSources,
  });

  const enabledSources = sources.filter((s) => s.is_enabled);

  const syncStatesQuery = useQuery({
    queryKey: ["sync-states", enabledSources.map((s) => s.id)],
    queryFn: async () => {
      const states: Record<number, SyncState> = {};

      for (const source of enabledSources) {
        try {
          states[source.id] = await getSyncState(source.id);
        } catch {
          // ignore
        }
      }

      return states;
    },
    enabled: enabledSources.length > 0,
    refetchInterval: 3000,
  });

  const syncMutation = useMutation({
    mutationFn: (sourceId: number) => triggerSync(sourceId),
    onMutate: (sourceId) => {
      setSyncingIds((prev) => new Set(prev).add(sourceId));
    },
    onSuccess: () => {
      showToast("Sync started", "success");
      queryClient.invalidateQueries({ queryKey: ["sync-states"] });
    },
    onError: () => {
      showToast("Failed to start sync", "error");
    },
    onSettled: (_data, _error, sourceId) => {
      setSyncingIds((prev) => {
        const next = new Set(prev);
        next.delete(sourceId);

        return next;
      });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (sourceId: number) => cancelSync(sourceId),
    onMutate: (sourceId) => {
      setCancellingIds((prev) => new Set(prev).add(sourceId));
    },
    onSuccess: () => {
      showToast("Cancellation requested — sync will stop after the current download finishes", "warning");
      queryClient.invalidateQueries({ queryKey: ["sync-states"] });
    },
    onError: () => {
      showToast("Failed to cancel sync", "error");
    },
    onSettled: (_data, _error, sourceId) => {
      setCancellingIds((prev) => {
        const next = new Set(prev);
        next.delete(sourceId);

        return next;
      });
    },
  });

  const syncStates = syncStatesQuery.data || {};

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        View sync status and trigger manual syncs for your configured sources.
      </p>

      {enabledSources.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <p className="text-gray-500 dark:text-gray-400">
            No enabled sources. Enable a source in the Sources settings to sync bookmarks.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
          {enabledSources.map((source) => (
            <SyncStatusCard
              key={source.id}
              source={source}
              syncState={syncStates[source.id] || null}
              onSync={(id) => syncMutation.mutate(id)}
              onCancel={(id) => cancelMutation.mutate(id)}
              isSyncing={syncingIds.has(source.id)}
              isCancelling={cancellingIds.has(source.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
