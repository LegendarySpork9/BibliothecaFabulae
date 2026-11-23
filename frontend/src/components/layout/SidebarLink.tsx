import clsx from "clsx";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";

interface SidebarLinkProps {
  to: string;
  icon: LucideIcon;
  label: string;
  collapsed: boolean;
}

export function SidebarLink({
  to,
  icon: Icon,
  label,
  collapsed,
}: SidebarLinkProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400 font-medium"
            : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        )
      }
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
    </NavLink>
  );
}
