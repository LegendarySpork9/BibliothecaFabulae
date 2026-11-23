import clsx from "clsx";
import {
  Archive,
  BellRing,
  HardDrive,
  Mail,
  Palette,
  UserCircle,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const tabs = [
  { to: "/settings/storage", label: "Storage", icon: HardDrive },
  { to: "/settings/theme", label: "Theme", icon: Palette },
  { to: "/settings/account", label: "Account", icon: UserCircle },
  { to: "/settings/backup", label: "Backup", icon: Archive },
  { to: "/settings/smtp", label: "SMTP", icon: Mail },
  { to: "/settings/notifications", label: "Notifications", icon: BellRing },
];

export function SettingsLayout() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Settings
      </h1>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
                isActive
                  ? "bg-indigo-600 text-white"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </div>

      <Outlet />
    </div>
  );
}
