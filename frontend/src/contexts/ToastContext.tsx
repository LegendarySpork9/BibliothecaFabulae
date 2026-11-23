import {
  createContext,
  useCallback,
  useState,
  type ReactNode,
} from "react";

import type { Severity } from "../types";

interface Toast {
  id: number;
  message: string;
  severity: Severity;
}

interface ToastContextType {
  showToast: (message: string, severity?: Severity) => void;
}

export const ToastContext = createContext<ToastContextType>({
  showToast: () => {},
});

let toastId = 0;

const severityStyles: Record<Severity, string> = {
  success: "bg-green-600 text-white",
  error: "bg-red-600 text-white",
  warning: "bg-yellow-500 text-black",
  info: "bg-blue-600 text-white",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, severity: Severity = "info") => {
      const id = ++toastId;
      setToasts((prev) => [...prev, { id, message, severity }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 5000);
    },
    []
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-lg px-4 py-3 shadow-lg text-sm font-medium transition-all animate-in fade-in slide-in-from-right ${severityStyles[toast.severity]}`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
