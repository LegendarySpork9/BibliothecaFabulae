import {
  Download,
  Plus,
  RefreshCw,
} from "lucide-react";
import { useContext, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { FicCard } from "../components/fics/FicCard";
import { ImportModal } from "../components/fics/ImportModal";
import { ToastContext } from "../contexts/ToastContext";
import { checkAllFicUpdates, getFics, getUpdateStatus, importFic } from "../api/fics";

export function LibraryPage() {
  const { showToast } = useContext(ToastContext);
  const queryClient = useQueryClient();

  const [showImport, setShowImport] = useState(false);
  const [sort, setSort] = useState("-date_archived");
  const [page, setPage] = useState(0);
  const pageSize = 24;

  const { data, isLoading } = useQuery({
    queryKey: ["fics", sort, page],
    queryFn: () => getFics({ sort, limit: pageSize, offset: page * pageSize }),
  });

  const importMutation = useMutation({
    mutationFn: (url: string) => importFic(url),
    onSuccess: () => {
      showToast("Import started. You'll be notified when it completes.", "success");
      setShowImport(false);
      queryClient.invalidateQueries({ queryKey: ["fics"] });
    },
    onError: () => {
      showToast("Failed to start import", "error");
    },
  });

  const [bulkCheckStarted, setBulkCheckStarted] = useState(false);
  const [serverConfirmedRunning, setServerConfirmedRunning] = useState(false);

  const updateCheckMutation = useMutation({
    mutationFn: checkAllFicUpdates,
    onMutate: () => {
      setBulkCheckStarted(true);
      setServerConfirmedRunning(false);
    },
    onSuccess: () => {
      showToast("Update check started for all fics", "success");
    },
    onError: () => {
      showToast("Failed to start update check", "error");
      setBulkCheckStarted(false);
    },
  });

  const { data: updateStatus } = useQuery({
    queryKey: ["update-status"],
    queryFn: getUpdateStatus,
    refetchInterval: 3000,
  });

  const isCheckRunningOnServer = updateStatus?.bulk_running ||
    (updateStatus?.checking_fic_ids?.length || 0) > 0;

  if (isCheckRunningOnServer && !serverConfirmedRunning) {
    setServerConfirmedRunning(true);
  }

  if (bulkCheckStarted && serverConfirmedRunning && !isCheckRunningOnServer) {
    setBulkCheckStarted(false);
    setServerConfirmedRunning(false);
  }

  const isCheckRunning = bulkCheckStarted || isCheckRunningOnServer;

  const fics = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Library
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} fic{total !== 1 ? "s" : ""} archived
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => updateCheckMutation.mutate()}
            disabled={updateCheckMutation.isPending || total === 0 || isCheckRunning}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${updateCheckMutation.isPending || isCheckRunning ? "animate-spin" : ""}`} />
            {isCheckRunning ? "Checking..." : "Check Updates"}
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Import
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(0); }}
          className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
        >
          <option value="-date_archived">Newest First</option>
          <option value="date_archived">Oldest First</option>
          <option value="title">Title A-Z</option>
          <option value="-title">Title Z-A</option>
          <option value="-word_count">Most Words</option>
          <option value="word_count">Fewest Words</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Loading...
        </div>
      ) : fics.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <Download className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Your library is empty. Import your first fic to get started.
          </p>
          <button
            onClick={() => setShowImport(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Import Fic
          </button>
        </div>
      ) : (
        <>
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {fics.map((fic) => (
              <FicCard key={fic.id} fic={fic} />
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

      {showImport && (
        <ImportModal
          onImport={(url) => importMutation.mutate(url)}
          onClose={() => setShowImport(false)}
          isLoading={importMutation.isPending}
        />
      )}
    </div>
  );
}
