import axios from "axios";
import { useState } from "react";

import { useToast } from "../../../hooks/useToast";

interface AccountStepProps {
  onNext: (data: { qr_code_base64: string; totp_secret: string }) => void;
}

export function AccountStep({ onNext }: AccountStepProps) {
  const { showToast } = useToast();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== passwordConfirm) {
      showToast("Passwords do not match", "error");

      return;
    }

    setLoading(true);

    try {
      const response = await axios.post("/api/setup/account", {
        username,
        password,
        password_confirm: passwordConfirm,
      });
      onNext(response.data);
    }

    catch (err) {
      const message =
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Failed to create account"
          : "Failed to create account";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
        Create Account
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Set up your username and password.
      </p>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Username
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          required
          minLength={3}
          maxLength={50}
          pattern="[a-zA-Z0-9_]+"
          title="Alphanumeric characters and underscores only"
          autoFocus
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          required
          minLength={12}

        />
        <p className="mt-1 text-xs text-gray-400">
          At least 12 characters with uppercase, lowercase, digit, and special
          character.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Confirm Password
        </label>
        <input
          type="password"
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          required

        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
      >
        {loading ? "Creating..." : "Next"}
      </button>
    </form>
  );
}
