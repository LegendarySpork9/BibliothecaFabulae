import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, requiresSetup } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (requiresSetup) {
    return <Navigate to="/setup" replace />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
