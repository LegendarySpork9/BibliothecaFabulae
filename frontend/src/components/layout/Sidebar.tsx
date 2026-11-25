import {
  Archive,
  Bell,
  BellRing,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Download,
  Globe,
  Globe2,
  RefreshCw,
  HardDrive,
  LayoutDashboard,
  LogOut,
  Mail,
  Palette,
  UserCircle,
  X,
} from "lucide-react";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

import { getUnreadCount } from "../../api/notifications";

import { useAuth } from "../../hooks/useAuth";
import { SidebarLink } from "./SidebarLink";

interface SidebarProps {
  open: boolean;
  collapsed: boolean;
  onClose: () => void;
  onToggleCollapse: () => void;
}

export function Sidebar({
  open,
  collapsed,
  onClose,
  onToggleCollapse,
}: SidebarProps) {
  const location = useLocation();
  const { logout } = useAuth();

  const { data: unreadData } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: getUnreadCount,
    refetchInterval: 10000,
  });

  const unreadCount = unreadData?.unread_count || 0;

  useEffect(() => {
    onClose();
  }, [location.pathname, onClose]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    if (open) {
      document.addEventListener("keydown", handleEscape);

      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [open, onClose]);

  const navContent = (
    <>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          <SidebarLink
            to="/dashboard"
            icon={LayoutDashboard}
            label="Dashboard"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/library"
            icon={BookOpen}
            label="Library"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/downloads"
            icon={Download}
            label="Downloads"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/sites"
            icon={Globe2}
            label="Supported Sites"
            collapsed={collapsed}
          />
          <div className="relative">
            <SidebarLink
              to="/notifications"
              icon={Bell}
              label="Notifications"
              collapsed={collapsed}
            />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 left-5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white pointer-events-none">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
          </div>

          <div className="pt-4 pb-2">
            {!collapsed && (
              <span className="px-3 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
                Settings
              </span>
            )}
          </div>

          <SidebarLink
            to="/settings/sources"
            icon={Globe}
            label="Sources"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/sync"
            icon={RefreshCw}
            label="Sync"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/storage"
            icon={HardDrive}
            label="Storage"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/theme"
            icon={Palette}
            label="Theme"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/account"
            icon={UserCircle}
            label="Account"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/backup"
            icon={Archive}
            label="Backup"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/smtp"
            icon={Mail}
            label="SMTP"
            collapsed={collapsed}
          />
          <SidebarLink
            to="/settings/notifications"
            icon={BellRing}
            label="Notification Prefs"
            collapsed={collapsed}
          />
        </nav>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 p-2">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>

        <button
          onClick={onToggleCollapse}
          className="hidden md:flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5 shrink-0" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5 shrink-0" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-xl transform transition-transform duration-300 md:hidden ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Logo" className="h-8 w-8" />
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Bibliotheca Fabulae
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex flex-col h-[calc(100%-3.5rem)]">{navContent}</div>
      </div>

      {/* Desktop sidebar */}
      <div
        className={`hidden md:flex md:flex-col md:fixed md:inset-y-0 md:left-0 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
          collapsed ? "md:w-16" : "md:w-64"
        }`}
      >
        <div className="flex h-14 items-center px-4 border-b border-gray-200 dark:border-gray-700">
          {!collapsed ? (
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="Logo" className="h-8 w-8" />
              <span className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
                Bibliotheca Fabulae
              </span>
            </div>
          ) : (
            <img src="/logo.png" alt="Logo" className="h-8 w-8 mx-auto" />
          )}
        </div>
        <div className="flex flex-col flex-1 overflow-hidden">{navContent}</div>
      </div>
    </>
  );
}
