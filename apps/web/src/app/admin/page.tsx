"use client";

import Link from "next/link";

export default function AdminPage() {
  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">Admin Panel</h1>

      <div className="space-y-4">
        <Link
          href="/admin/unresolved"
          className="block rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all shadow-sm hover:shadow-md"
        >
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Unresolved Locations
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            Review and resolve event locations that couldn&apos;t be automatically
            matched to venues.
          </p>
        </Link>
      </div>
    </div>
  );
}
