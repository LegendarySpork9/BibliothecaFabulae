import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthGuard } from "./components/guards/AuthGuard";
import { SetupGuard } from "./components/guards/SetupGuard";
import { AppLayout } from "./components/layout/AppLayout";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ToastProvider } from "./contexts/ToastContext";
import { DashboardPage } from "./pages/DashboardPage";
import { DownloadsPage } from "./pages/DownloadsPage";
import { FicDetailPage } from "./pages/FicDetailPage";
import { LibraryPage } from "./pages/LibraryPage";
import { LoginPage } from "./pages/LoginPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { SitesPage } from "./pages/SitesPage";
import { AccountSettingsPage } from "./pages/settings/AccountSettingsPage";
import { BackupSettingsPage } from "./pages/settings/BackupSettingsPage";
import { NotificationPrefsPage } from "./pages/settings/NotificationPrefsPage";
import { SettingsLayout } from "./pages/settings/SettingsLayout";
import { SmtpSettingsPage } from "./pages/settings/SmtpSettingsPage";
import { SourcesSettingsPage } from "./pages/settings/SourcesSettingsPage";
import { StorageSettingsPage } from "./pages/settings/StorageSettingsPage";
import { SyncSettingsPage } from "./pages/settings/SyncSettingsPage";
import { ThemeSettingsPage } from "./pages/settings/ThemeSettingsPage";
import { SetupWizard } from "./pages/setup/SetupWizard";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter>
            <AuthProvider>
              <Routes>
                <Route
                  path="/setup/*"
                  element={
                    <SetupGuard>
                      <SetupWizard />
                    </SetupGuard>
                  }
                />
                <Route path="/login" element={<LoginPage />} />
                <Route
                  element={
                    <AuthGuard>
                      <AppLayout />
                    </AuthGuard>
                  }
                >
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/sites" element={<SitesPage />} />
                  <Route path="/downloads" element={<DownloadsPage />} />
                  <Route path="/library" element={<LibraryPage />} />
                  <Route path="/library/:ficId" element={<FicDetailPage />} />
                  <Route
                    path="/notifications"
                    element={<NotificationsPage />}
                  />
                  <Route path="/settings" element={<SettingsLayout />}>
                    <Route index element={<Navigate to="storage" replace />} />
                    <Route path="storage" element={<StorageSettingsPage />} />
                    <Route path="theme" element={<ThemeSettingsPage />} />
                    <Route path="account" element={<AccountSettingsPage />} />
                    <Route path="backup" element={<BackupSettingsPage />} />
                    <Route path="smtp" element={<SmtpSettingsPage />} />
                    <Route path="sources" element={<SourcesSettingsPage />} />
                    <Route path="sync" element={<SyncSettingsPage />} />
                    <Route
                      path="notifications"
                      element={<NotificationPrefsPage />}
                    />
                  </Route>
                  <Route
                    path="/"
                    element={<Navigate to="/dashboard" replace />}
                  />
                </Route>
              </Routes>
            </AuthProvider>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
