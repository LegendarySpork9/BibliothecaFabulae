import {
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Globe,
  Key,
  RefreshCw,
  Search,
  Settings,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getSupportedSites } from "../api/fics";
import type { SupportedSiteInfo } from "../types/fic";

function CapabilityBadge({
  supported,
  label,
}: {
  supported: boolean;
  label: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${
        supported
          ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300"
          : "bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500"
      }`}
    >
      {supported ? (
        <CheckCircle className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      {label}
    </span>
  );
}

function SiteRow({ site }: { site: SupportedSiteInfo }) {
  const [expanded, setExpanded] = useState(false);
  const hasAuthHelp = site.auth_help && Object.keys(site.auth_help).length > 0;
  const hasConfigHelp = site.config_help && Object.keys(site.config_help).length > 0;
  const hasHelp = hasAuthHelp || hasConfigHelp;

  return (
    <div className="px-6 py-4">
      <div className="flex items-center gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {site.name}
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
              {site.domain}
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5 mt-1.5">
            <CapabilityBadge supported={site.manual_import} label="Manual Import" />
            <CapabilityBadge supported={site.update_checking} label="Update Checking" />
            {site.list_sync ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
                <RefreshCw className="h-3 w-3" />
                {site.sync_label}
              </span>
            ) : (
              <CapabilityBadge supported={false} label="List Sync" />
            )}
            {site.auth_required && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">
                <Key className="h-3 w-3" />
                Auth Required
              </span>
            )}
            {site.config_required && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-cyan-100 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300">
                <Settings className="h-3 w-3" />
                Config Required
              </span>
            )}
          </div>

          {site.sync_description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {site.sync_description}
            </p>
          )}
        </div>

        {hasHelp && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 shrink-0"
            title="Setup instructions"
          >
            {expanded ? (
              <ChevronDown className="h-5 w-5" />
            ) : (
              <ChevronRight className="h-5 w-5" />
            )}
          </button>
        )}
      </div>

      {expanded && hasHelp && (
        <div className="mt-3 space-y-4 pl-1 border-l-2 border-indigo-200 dark:border-indigo-800 ml-1">
          {hasAuthHelp && (
            <div className="space-y-3">
              <p className="pl-3 text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                Authentication
              </p>
              {Object.entries(site.auth_help!).map(([authType, help]) => (
                <div key={authType} className="pl-3">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300 capitalize">
                    {authType} auth
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {help.instructions}
                  </p>
                  {help.expiry && (
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                      Cookie expiry: {help.expiry}
                    </p>
                  )}
                  <div className="mt-1 px-2 py-1.5 rounded bg-gray-100 dark:bg-gray-700/50">
                    <code className="text-xs text-gray-600 dark:text-gray-300 break-all">
                      {help.format}
                    </code>
                  </div>
                </div>
              ))}
            </div>
          )}
          {hasConfigHelp && (
            <div className="space-y-3">
              <p className="pl-3 text-xs font-semibold text-cyan-600 dark:text-cyan-400 uppercase tracking-wide">
                Configuration
              </p>
              {Object.entries(site.config_help!).map(([field, help]) => (
                <div key={field} className="pl-3">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {field}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {help.instructions}
                  </p>
                  <div className="mt-1 px-2 py-1.5 rounded bg-gray-100 dark:bg-gray-700/50">
                    <code className="text-xs text-gray-600 dark:text-gray-300 break-all">
                      {help.format}
                    </code>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function SitesPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "sync" | "manual">("all");

  const { data: sites = [], isLoading } = useQuery({
    queryKey: ["supported-sites-directory"],
    queryFn: getSupportedSites,
  });

  const filtered = sites.filter((site) => {
    if (filter === "sync" && !site.list_sync) {
      return false;
    }

    if (filter === "manual" && site.list_sync) {
      return false;
    }

    if (search) {
      const q = search.toLowerCase();

      return (
        site.name.toLowerCase().includes(q) ||
        site.domain.toLowerCase().includes(q)
      );
    }

    return true;
  });

  const syncCount = sites.filter((s) => s.list_sync).length;
  const manualCount = sites.filter((s) => !s.list_sync).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Supported Sites
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {sites.length} sites supported — {syncCount} with automated sync, {manualCount} manual import only.
          All sites support update checking once a fic is archived.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search sites..."
            className="w-full pl-10 pr-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
          />
        </div>

        <div className="flex gap-1">
          {[
            { value: "all" as const, label: `All (${sites.length})` },
            { value: "sync" as const, label: `Automated Sync (${syncCount})` },
            { value: "manual" as const, label: `Manual Only (${manualCount})` },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                filter === f.value
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Loading...
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <Globe className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {search ? `No sites matching "${search}"` : "No sites found."}
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
          {filtered.map((site) => (
            <SiteRow key={site.domain} site={site} />
          ))}
        </div>
      )}
    </div>
  );
}
