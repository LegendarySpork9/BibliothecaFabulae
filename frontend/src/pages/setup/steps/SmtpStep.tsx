import axios from "axios";
import { useState } from "react";

import { useToast } from "../../../hooks/useToast";

interface SmtpStepProps {
  onNext: (configured: boolean) => void;
  onBack: () => void;
}

export function SmtpStep({ onNext, onBack }: SmtpStepProps) {
  const { showToast } = useToast();

  const [host, setHost] = useState("");
  const [port, setPort] = useState("587");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [useTls, setUseTls] = useState(true);
  const [fromAddress, setFromAddress] = useState("");
  const [toAddress, setToAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [tested, setTested] = useState(false);

  const handleTest = async () => {
    setTesting(true);

    try {
      const response = await axios.post("/api/setup/smtp/test", {
        smtp_host: host,
        smtp_port: parseInt(port),
        smtp_username: username,
        smtp_password: password,
        smtp_use_tls: useTls,
      });

      if (response.data.success) {
        showToast("Connection successful!", "success");
        setTested(true);
      } else {
        showToast(response.data.message || "Test failed", "error");
        setTested(false);
      }
    }

    catch {
      showToast("Test failed", "error");
      setTested(false);
    }

    finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);

    try {
      await axios.post("/api/setup/smtp", {
        smtp_host: host,
        smtp_port: parseInt(port),
        smtp_username: username,
        smtp_password: password,
        smtp_use_tls: useTls,
        smtp_from_address: fromAddress,
        smtp_to_address: toAddress,
      });
      showToast("SMTP configured", "success");
      onNext(true);
    }

    catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Failed to save SMTP settings"
          : "Failed to save SMTP settings";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
        Email Notifications
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Configure SMTP for email notifications. This is optional — you can set
        it up later in settings.
      </p>

      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2 sm:col-span-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            SMTP Host
          </label>
          <input
            type="text"
            value={host}
            onChange={(e) => { setHost(e.target.value); setTested(false); }}
            placeholder="smtp.gmail.com"
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="col-span-2 sm:col-span-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Port
          </label>
          <input
            type="number"
            value={port}
            onChange={(e) => { setPort(e.target.value); setTested(false); }}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => { setUsername(e.target.value); setTested(false); }}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setTested(false); }}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            From Address
          </label>
          <input
            type="email"
            value={fromAddress}
            onChange={(e) => setFromAddress(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            To Address
          </label>
          <input
            type="email"
            value={toAddress}
            onChange={(e) => setToAddress(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
        <input
          type="checkbox"
          checked={useTls}
          onChange={(e) => { setUseTls(e.target.checked); setTested(false); }}
          className="rounded border-gray-300 dark:border-gray-600"
        />
        Use TLS
      </label>

      {tested && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 text-sm text-green-700 dark:text-green-300">
          Connection tested successfully.
        </div>
      )}

      <div className="flex gap-3 flex-wrap">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleTest}
          disabled={testing || !host}
          className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {testing ? "Testing..." : "Test Connection"}
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={loading || !host || !tested}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Saving..." : "Save & Next"}
        </button>
        <button
          type="button"
          onClick={() => onNext(false)}
          className="rounded-lg border border-indigo-300 dark:border-indigo-700 px-4 py-2 text-indigo-600 dark:text-indigo-400 font-medium hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
        >
          Skip
        </button>
      </div>
    </div>
  );
}
