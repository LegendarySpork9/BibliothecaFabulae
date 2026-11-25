import {
  AlertTriangle,
  BookOpen,
  CheckCircle,
  Clock,
} from "lucide-react";
import { Link } from "react-router-dom";

import type { FicSummary } from "../../types/fic";

interface FicCardProps {
  fic: FicSummary;
}

const siteLabels: Record<string, string> = {
  ao3: "AO3",
  ffnet: "FFNet",
  wattpad: "Wattpad",
  royalroad: "Royal Road",
  spacebattles: "SpaceBattles",
  sufficientvelocity: "SV",
  scribblehub: "Scribble Hub",
  fimfiction: "Fimfiction",
  quotev: "Quotev",
};

function formatWordCount(count: number | null): string {
  if (!count) {
    return "—";
  }

  if (count >= 1_000_000) {
    return `${(count / 1_000_000).toFixed(1)}M`;
  }

  if (count >= 1_000) {
    return `${(count / 1_000).toFixed(0)}K`;
  }

  return count.toString();
}

export function FicCard({ fic }: FicCardProps) {
  return (
    <Link
      to={`/library/${fic.id}`}
      className="block bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
          {fic.title}
        </h3>
        <div className="flex items-center gap-1 shrink-0">
          {!fic.is_source_available && (
            <span title="Unavailable at source">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </span>
          )}
          {fic.is_complete ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <Clock className="h-4 w-4 text-yellow-500" />
          )}
        </div>
      </div>

      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        {fic.authors.map((a) => a.name).join(", ") || "Unknown Author"}
      </p>

      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
          {siteLabels[fic.source_site] || fic.source_site}
        </span>
        {fic.rating && (
          <span className="px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300">
            {fic.rating}
          </span>
        )}
        <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1 ml-1">
          <BookOpen className="h-3 w-3" />
          {fic.chapter_count || 0} ch
        </span>
        <span className="text-gray-500 dark:text-gray-400">
          {formatWordCount(fic.word_count)} words
        </span>
      </div>
    </Link>
  );
}
