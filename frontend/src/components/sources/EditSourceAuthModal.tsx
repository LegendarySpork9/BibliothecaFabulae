import { X } from "lucide-react";
import { useState } from "react";

import type { Source, SupportedSite } from "../../types/source";

interface EditSourceAuthModalProps {
  source: Source;
  supportedSites: SupportedSite[];
  onSave: (sourceId: number, authType: string, authData?: string) => void;
  onClose: () => void;
  isSaving: boolean;
}

export function EditSourceAuthModal({
  source,
  supportedSites,
  onSave,
  onClose,
  isSaving,
}: EditSourceAuthModalProps) {
  const siteInfo = supportedSites.find((s) => s.site_key === source.site_key);
  const authTypes = siteInfo?.auth_types || ["none"];

  const [authType, setAuthType] = useState<string>(source.auth_type);
  const [authData, setAuthData] = useState<string>("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(source.id, authType, authData || undefined);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Edit Auth &mdash; {source.label}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Authentication Type
            </label>
            <select
              value={authType}
              onChange={(e) => setAuthType(e.target.value)}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
            >
              {authTypes.map((type) => (
                <option key={type} value={type}>
                  {type === "config" ? "Site Configuration" : type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
              <option value="none">None</option>
            </select>
          </div>

          {authType !== "none" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {authType === "credentials"
                  ? "Credentials (JSON: username, password)"
                  : authType === "cookies"
                    ? "Cookie String"
                    : authType === "config"
                      ? "Configuration (JSON)"
                      : "API Key"}
              </label>
              <textarea
                value={authData}
                onChange={(e) => setAuthData(e.target.value)}
                rows={3}
                placeholder={
                  source.auth_configured
                    ? "Leave empty to keep current settings"
                    : authType === "credentials"
                      ? '{"username": "...", "password": "..."}'
                      : authType === "cookies"
                        ? "name=value; name2=value2 (e.g. cf_clearance=abc123)"
                        : authType === "config"
                          ? '{"profile_url": "..."} or {"bookshelf_url": "..."}'
                          : "Enter your API key..."
                }
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm font-mono"
              />
              {source.auth_configured && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Leave empty to keep current credentials
                </p>
              )}
            </div>
          )}

          {isSaving && (
            <div className="flex items-center gap-2 text-sm text-indigo-600 dark:text-indigo-400">
              <div className="h-4 w-4 border-2 border-indigo-600 dark:border-indigo-400 border-t-transparent rounded-full animate-spin" />
              Saving and verifying credentials...
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
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? "Verifying..." : "Save & Verify"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
