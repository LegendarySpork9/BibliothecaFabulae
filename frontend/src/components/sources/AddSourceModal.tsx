import { X } from "lucide-react";
import { useState } from "react";

import type { SupportedSite } from "../../types/source";

interface AddSourceModalProps {
  supportedSites: SupportedSite[];
  existingSiteKeys: string[];
  onAdd: (siteKey: string, authType: string, authData?: string, configData?: string) => void;
  onClose: () => void;
}

export function AddSourceModal({
  supportedSites,
  existingSiteKeys,
  onAdd,
  onClose,
}: AddSourceModalProps) {
  const [selectedSite, setSelectedSite] = useState<string>("");
  const [authType, setAuthType] = useState<string>("none");
  const [authData, setAuthData] = useState<string>("");
  const [configData, setConfigData] = useState<string>("");

  const availableSites = supportedSites.filter(
    (s) => !existingSiteKeys.includes(s.site_key)
  );

  const selectedSiteInfo = supportedSites.find(
    (s) => s.site_key === selectedSite
  );

  const handleSiteChange = (siteKey: string) => {
    setSelectedSite(siteKey);
    const site = supportedSites.find((s) => s.site_key === siteKey);
    setAuthType(site?.auth_types[0] || "none");
    setAuthData("");
    setConfigData("");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd(selectedSite, authType, authData || undefined, configData || undefined);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Add Source
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
              Site
            </label>
            <select
              value={selectedSite}
              onChange={(e) => handleSiteChange(e.target.value)}
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
              required
            >
              <option value="">Select a site...</option>
              {availableSites.map((site) => (
                <option key={site.site_key} value={site.site_key}>
                  {site.label}
                </option>
              ))}
            </select>
          </div>

          {selectedSiteInfo && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Authentication Type
                </label>
                <select
                  value={authType}
                  onChange={(e) => setAuthType(e.target.value)}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm"
                >
                  {selectedSiteInfo.auth_types.map((type) => (
                    <option key={type} value={type}>
                      {type === "config" ? "Site Configuration" : type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {authType !== "none" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {authType === "credentials"
                      ? "Credentials (JSON: username, password)"
                      : authType === "cookies"
                        ? "Cookie String"
                        : "API Key"}
                  </label>
                  <textarea
                    value={authData}
                    onChange={(e) => setAuthData(e.target.value)}
                    rows={3}
                    placeholder={
                      authType === "credentials"
                        ? '{"username": "...", "password": "..."}'
                        : authType === "cookies"
                          ? "name=value; name2=value2 (e.g. cf_clearance=abc123)"
                          : "Enter your API key..."
                    }
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm font-mono"
                  />
                </div>
              )}

              {selectedSiteInfo.config_fields && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Site Configuration (JSON)
                  </label>
                  {Object.entries(selectedSiteInfo.config_fields).map(([key, desc]) => (
                    <p key={key} className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                      <span className="font-mono text-indigo-600 dark:text-indigo-400">{key}</span> — {desc}
                    </p>
                  ))}
                  <textarea
                    value={configData}
                    onChange={(e) => setConfigData(e.target.value)}
                    rows={2}
                    placeholder={`{"${Object.keys(selectedSiteInfo.config_fields)[0]}": "..."}`}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm font-mono"
                  />
                </div>
              )}
            </>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedSite}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Add Source
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
