import clsx from "clsx";
import { Moon, Sun } from "lucide-react";

import { useTheme } from "../../hooks/useTheme";

export function ThemeSettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
        Choose Theme
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => setTheme("light")}
          className={clsx(
            "rounded-xl border-2 p-4 transition-all",
            theme === "light"
              ? "border-indigo-600 ring-2 ring-indigo-100 dark:ring-indigo-900"
              : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
          )}
        >
          <div className="rounded-lg bg-white border border-gray-200 p-3 mb-3">
            <div className="h-2 w-16 rounded bg-gray-200 mb-2" />
            <div className="h-2 w-24 rounded bg-gray-100" />
          </div>
          <div className="flex items-center justify-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <Sun className="h-4 w-4" />
            Light
          </div>
        </button>

        <button
          onClick={() => setTheme("dark")}
          className={clsx(
            "rounded-xl border-2 p-4 transition-all",
            theme === "dark"
              ? "border-indigo-600 ring-2 ring-indigo-100 dark:ring-indigo-900"
              : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
          )}
        >
          <div className="rounded-lg bg-gray-900 border border-gray-700 p-3 mb-3">
            <div className="h-2 w-16 rounded bg-gray-700 mb-2" />
            <div className="h-2 w-24 rounded bg-gray-800" />
          </div>
          <div className="flex items-center justify-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <Moon className="h-4 w-4" />
            Dark
          </div>
        </button>
      </div>
    </div>
  );
}
