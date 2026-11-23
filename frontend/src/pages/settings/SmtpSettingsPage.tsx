import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { CheckCircle, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { getSettings, testSmtp, updateSmtp } from "../../api/settings";
import { useToast } from "../../hooks/useToast";

export function SmtpSettingsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [host, setHost] = useState("");
  const [port, setPort] = useState("587");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [useTls, setUseTls] = useState(true);
  const [fromAddress, setFromAddress] = useState("");
  const [toAddress, setToAddress] = useState("");

  useEffect(() => {
    if (settings) {
      setHost(settings.smtp_host || "");
      setPort(String(settings.smtp_port || 587));
      setUsername(settings.smtp_username || "");
      setUseTls(settings.smtp_use_tls);
      setFromAddress(settings.smtp_from_address || "");
      setToAddress(settings.smtp_to_address || "");
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateSmtp({
        smtp_host: host,
        smtp_port: parseInt(port),
        smtp_username: username,
        smtp_password: password,
        smtp_use_tls: useTls,
        smtp_from_address: fromAddress,
        smtp_to_address: toAddress,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      showToast("SMTP settings saved", "success");
      setPassword("");
    },
    onError: () => showToast("Failed to save SMTP settings", "error"),
  });

  const testMutation = useMutation({
    mutationFn: testSmtp,
    onSuccess: (data) => {
      if (data.success) {
        showToast("Test email sent!", "success");
      } else {
        showToast(data.message || "Test failed", "error");
      }
    },
    onError: () => showToast("Test failed", "error"),
  });

  const isConfigured = settings?.smtp_password_configured;

  return (
    <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          SMTP Configuration
        </h3>
        {isConfigured ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 dark:bg-green-900 px-2 py-0.5 text-xs text-green-700 dark:text-green-300">
            <CheckCircle className="h-3 w-3" /> Configured
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 dark:bg-gray-700 px-2 py-0.5 text-xs text-gray-500 dark:text-gray-400">
            <XCircle className="h-3 w-3" /> Not configured
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Host</label>
          <input type="text" value={host} onChange={(e) => setHost(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Port</label>
          <input type="number" value={port} onChange={(e) => setPort(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={isConfigured ? "••••••••" : ""} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From</label>
          <input type="email" value={fromAddress} onChange={(e) => setFromAddress(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To</label>
          <input type="email" value={toAddress} onChange={(e) => setToAddress(e.target.value)} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
        <input type="checkbox" checked={useTls} onChange={(e) => setUseTls(e.target.checked)} className="rounded border-gray-300 dark:border-gray-600" />
        Use TLS
      </label>

      <div className="flex gap-3">
        <button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50">Save</button>
        <button onClick={() => testMutation.mutate()} disabled={testMutation.isPending || !isConfigured} className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Test</button>
      </div>
    </div>
  );
}
