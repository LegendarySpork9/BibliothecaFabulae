import axios from "axios";
import { useState } from "react";

import { useToast } from "../../../hooks/useToast";

interface TotpStepProps {
  qrCodeBase64: string;
  totpSecret: string;
  onNext: () => void;
  onBack: () => void;
}

export function TotpStep({
  qrCodeBase64,
  totpSecret,
  onNext,
  onBack,
}: TotpStepProps) {
  const { showToast } = useToast();

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);

    try {
      await axios.post("/api/setup/verify-totp", { totp_code: code });
      onNext();
    }

    catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Invalid code"
          : "Invalid code";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
        Two-Factor Authentication
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Scan this QR code with your authenticator app, then enter the code.
      </p>

      <div className="flex justify-center">
        <img
          src={`data:image/png;base64,${qrCodeBase64}`}
          alt="TOTP QR Code"
          className="h-48 w-48 rounded-lg bg-white p-2"
        />
      </div>

      <details className="text-sm">
        <summary className="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
          Can't scan? Enter manually
        </summary>
        <code className="mt-2 block rounded bg-gray-100 dark:bg-gray-700 p-2 text-xs break-all text-gray-700 dark:text-gray-300">
          {totpSecret}
        </code>
      </details>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Verification Code
        </label>
        <input
          type="text"
          inputMode="numeric"
          pattern="[0-9]{6}"
          maxLength={6}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-center text-2xl tracking-widest text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          required
          autoFocus
        />
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
          type="submit"
          disabled={loading || code.length !== 6}
          className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Verifying..." : "Verify"}
        </button>
      </div>
    </form>
  );
}
