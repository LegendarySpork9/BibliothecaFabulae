import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Cloud, Shield, Trash2 } from "lucide-react";
import { useState } from "react";

import { getSessions, revokeSession } from "../../api/auth";
import client from "../../api/client";
import {
  changePassword,
  confirmNewTotp,
  getAccount,
  getSettings,
  regenerateTotp,
} from "../../api/settings";
import { useToast } from "../../hooks/useToast";

export function AccountSettingsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const { data: account } = useQuery({ queryKey: ["account"], queryFn: getAccount });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const { data: sessions } = useQuery({ queryKey: ["sessions"], queryFn: getSessions });

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPw, setConfirmPw] = useState("");

  const [totpPending, setTotpPending] = useState<{
    qr_code_base64: string;
    totp_secret: string;
  } | null>(null);
  const [totpCode, setTotpCode] = useState("");

  const passwordMutation = useMutation({
    mutationFn: () =>
      changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: confirmPw,
      }),
    onSuccess: () => {
      showToast("Password updated", "success");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPw("");
    },
    onError: () => showToast("Failed to change password", "error"),
  });

  const regenerateMutation = useMutation({
    mutationFn: regenerateTotp,
    onSuccess: (data) => setTotpPending(data),
    onError: () => showToast("Failed to regenerate TOTP", "error"),
  });

  const confirmTotpMutation = useMutation({
    mutationFn: () => confirmNewTotp(totpCode, totpPending!.totp_secret),
    onSuccess: () => {
      showToast("TOTP updated", "success");
      setTotpPending(null);
      setTotpCode("");
    },
    onError: () => showToast("Invalid code", "error"),
  });

  const revokeMutation = useMutation({
    mutationFn: revokeSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      showToast("Session revoked", "success");
    },
  });

  return (
    <div className="space-y-6">
      {/* Account Info */}
      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Account
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Username: <span className="font-medium text-gray-900 dark:text-gray-100">{account?.username}</span>
        </p>
      </div>

      {/* Cloudflare Trust */}
      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-2">
          <Cloud className="h-5 w-5" />
          Cloudflare Zero Trust
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          When enabled, the login page skips username and password — only the TOTP code is required.
          Use this when the site is behind Cloudflare Zero Trust which handles identity verification.
        </p>
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={settings?.cloudflare_trust_enabled ?? false}
            onChange={async (e) => {
              const enabled = e.target.checked;

              try {
                await client.patch("/settings/cloudflare-trust", { enabled });
                queryClient.invalidateQueries({ queryKey: ["settings"] });
                showToast(enabled ? "Cloudflare trust enabled" : "Cloudflare trust disabled", "success");
              }

              catch {
                showToast("Failed to update", "error");
              }
            }}
            className="rounded border-gray-300 dark:border-gray-600 h-5 w-5"
          />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Skip username/password login (TOTP only)
          </span>
        </label>
      </div>

      {/* Change Password */}
      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Change Password
        </h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            passwordMutation.mutate();
          }}
          className="space-y-3 max-w-sm"
        >
          <input
            type="password"
            placeholder="Current password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            required
          />
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            required
            minLength={12}
          />
          <input
            type="password"
            placeholder="Confirm new password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            required
          />
          <button
            type="submit"
            disabled={passwordMutation.isPending}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Update Password
          </button>
        </form>
      </div>

      {/* TOTP */}
      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Two-Factor Authentication
        </h3>

        {totpPending ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Scan this new QR code, then enter the verification code.
            </p>
            <img
              src={`data:image/png;base64,${totpPending.qr_code_base64}`}
              alt="New TOTP QR"
              className="h-40 w-40 bg-white p-2 rounded"
            />
            <div className="flex gap-2 max-w-xs">
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder="000000"
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-center text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={() => confirmTotpMutation.mutate()}
                disabled={totpCode.length !== 6}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Confirm
              </button>
            </div>
            <button
              onClick={() => setTotpPending(null)}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => regenerateMutation.mutate()}
            className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Regenerate TOTP Secret
          </button>
        )}
      </div>

      {/* Sessions */}
      <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Active Sessions
        </h3>
        {sessions?.length ? (
          <div className="space-y-2">
            {sessions.map((s: { id: number; device_name: string | null; is_current: boolean; created_at: string | null; last_used_at: string | null }) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 p-3"
              >
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {s.device_name || "Unknown device"}
                  </span>
                  {s.is_current && (
                    <span className="ml-2 inline-flex items-center rounded-full bg-green-100 dark:bg-green-900 px-2 py-0.5 text-xs text-green-700 dark:text-green-300">
                      Current
                    </span>
                  )}
                  <p className="text-xs text-gray-400 mt-0.5">
                    Last used: {s.last_used_at ? new Date(s.last_used_at).toLocaleString() : "Never"}
                  </p>
                </div>
                {!s.is_current && (
                  <button
                    onClick={() => revokeMutation.mutate(s.id)}
                    className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No active sessions.</p>
        )}
      </div>
    </div>
  );
}
