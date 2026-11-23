import axios from "axios";
import { CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";

import { useToast } from "../../../hooks/useToast";

interface SummaryStepProps {
  storagePath: string;
  smtpConfigured: boolean;
  onComplete: (accessToken: string) => void;
  onBack: () => void;
}

export function SummaryStep({
  storagePath,
  smtpConfigured,
  onComplete,
  onBack,
}: SummaryStepProps) {
  const { showToast } = useToast();

  const [loading, setLoading] = useState(false);

  const handleComplete = async () => {
    setLoading(true);

    try {
      const response = await axios.post("/api/setup/complete");
      showToast("Setup complete!", "success");
      onComplete(response.data.access_token);
    }

    catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Failed to complete setup"
          : "Failed to complete setup";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
        Setup Summary
      </h2>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
          <span className="text-gray-700 dark:text-gray-300">
            Account created with 2FA enabled
          </span>
        </div>
        <div className="flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
          <span className="text-gray-700 dark:text-gray-300">
            Storage: <code className="text-sm bg-gray-100 dark:bg-gray-700 px-1 rounded">{storagePath}</code>
          </span>
        </div>
        <div className="flex items-center gap-3">
          {smtpConfigured ? (
            <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
          ) : (
            <XCircle className="h-5 w-5 text-gray-400 shrink-0" />
          )}
          <span className="text-gray-700 dark:text-gray-300">
            Email notifications: {smtpConfigured ? "Configured" : "Skipped"}
          </span>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleComplete}
          disabled={loading}
          className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Completing..." : "Complete Setup"}
        </button>
      </div>
    </div>
  );
}
