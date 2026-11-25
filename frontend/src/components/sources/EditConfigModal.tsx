import { Settings, X } from "lucide-react";
import { useState } from "react";

import type { Source } from "../../types/source";

interface EditConfigModalProps {
  source: Source;
  onSave: (sourceId: number, configData: string) => void;
  onClose: () => void;
  isSaving: boolean;
}

export function EditConfigModal({
  source,
  onSave,
  onClose,
  isSaving,
}: EditConfigModalProps) {
  const [configData, setConfigData] = useState("");
  const configFields = source.config_fields || {};
  const fieldEntries = Object.entries(configFields);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (configData.trim()) {
      onSave(source.id, configData.trim());
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configure &mdash; {source.label}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {fieldEntries.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                This site needs the following configuration for sync:
              </p>
              {fieldEntries.map(([key, description]) => (
                <div
                  key={key}
                  className="px-3 py-2 rounded bg-gray-50 dark:bg-gray-700/50 text-sm"
                >
                  <span className="font-mono text-indigo-600 dark:text-indigo-400">{key}</span>
                  <span className="text-gray-500 dark:text-gray-400"> — {description}</span>
                </div>
              ))}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Configuration (JSON)
            </label>
            <textarea
              value={configData}
              onChange={(e) => setConfigData(e.target.value)}
              rows={3}
              placeholder={
                fieldEntries.length > 0
                  ? `{"${fieldEntries[0][0]}": "..."}`
                  : '{"key": "value"}'
              }
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm font-mono"
            />
            {source.config_configured && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Configuration is already set. Submit to replace it.
              </p>
            )}
          </div>

          {isSaving && (
            <div className="flex items-center gap-2 text-sm text-indigo-600 dark:text-indigo-400">
              <div className="h-4 w-4 border-2 border-indigo-600 dark:border-indigo-400 border-t-transparent rounded-full animate-spin" />
              Saving configuration...
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!configData.trim() || isSaving}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? "Saving..." : "Save Config"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
