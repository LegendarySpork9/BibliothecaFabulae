import { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import client, { setAccessToken } from "../api/client";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";

export function LoginPage() {
  const { isAuthenticated, requiresSetup, login, verifyTotp } = useAuth();
  const { showToast } = useToast();

  const [step, setStep] = useState<"loading" | "credentials" | "totp" | "totp-only">("loading");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [tempToken, setTempToken] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    client.get("/auth/mode").then((res) => {
      setStep(res.data.cloudflare_trust ? "totp-only" : "credentials");
    }).catch(() => setStep("credentials"));
  }, []);

  if (requiresSetup) {
    return <Navigate to="/setup" replace />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);

    try {
      const token = await login(username, password);
      setTempToken(token);
      setStep("totp");
    }

    catch (err) {
      const message =
        err instanceof AxiosError
          ? err.response?.data?.detail || "Login failed"
          : "Login failed";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  const handleTotp = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);

    try {
      await verifyTotp(tempToken, totpCode, rememberDevice);
    }

    catch (err) {
      const message =
        err instanceof AxiosError
          ? err.response?.data?.detail || "Invalid TOTP code"
          : "Invalid TOTP code";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  const handleTotpOnly = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);

    try {
      const response = await client.post("/auth/totp-only", {
        totp_code: totpCode,
        remember_device: rememberDevice,
      });
      setAccessToken(response.data.access_token);
      window.location.href = "/dashboard";
    }

    catch (err) {
      const message =
        err instanceof AxiosError
          ? err.response?.data?.detail || "Invalid TOTP code"
          : "Invalid TOTP code";
      showToast(message, "error");
    }

    finally {
      setLoading(false);
    }
  };

  if (step === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <img src="/logo.png" alt="Bibliotheca Fabulae" className="h-16 w-16 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100 mb-2">
          Bibliotheca Fabulae
        </h1>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-8">
          {step === "credentials"
            ? "Sign in to your library"
            : "Enter your authentication code"}
        </p>

        {step === "credentials" && (
          <form onSubmit={handleLogin} className="space-y-4">
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
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        )}

        {step === "totp" && (
          <form onSubmit={handleTotp} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                TOTP Code
              </label>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-center text-2xl tracking-widest text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                autoFocus
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <input
                type="checkbox"
                checked={rememberDevice}
                onChange={(e) => setRememberDevice(e.target.checked)}
                className="rounded border-gray-300 dark:border-gray-600"
              />
              Remember this device
            </label>
            <button
              type="submit"
              disabled={loading || totpCode.length !== 6}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Verifying..." : "Verify"}
            </button>
            <button
              type="button"
              onClick={() => {
                setStep("credentials");
                setTotpCode("");
              }}
              className="w-full text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Back to login
            </button>
          </form>
        )}

        {step === "totp-only" && (
          <form onSubmit={handleTotpOnly} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                TOTP Code
              </label>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-center text-2xl tracking-widest text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
                autoFocus
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <input
                type="checkbox"
                checked={rememberDevice}
                onChange={(e) => setRememberDevice(e.target.checked)}
                className="rounded border-gray-300 dark:border-gray-600"
              />
              Remember this device
            </label>
            <button
              type="submit"
              disabled={loading || totpCode.length !== 6}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Verifying..." : "Verify"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
