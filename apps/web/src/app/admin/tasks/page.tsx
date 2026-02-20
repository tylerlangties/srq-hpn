"use client";

import { useEffect, useMemo, useState } from "react";

import { useAdminGuard } from "@/app/hooks/useAdminGuard";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import type { TaskRunDashboardOut } from "@/types/admin";

function formatDateTime(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(runtimeMs: number | null): string {
  if (runtimeMs === null) return "-";
  if (runtimeMs < 1000) return `${runtimeMs} ms`;
  const seconds = runtimeMs / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
}

export default function AdminTaskRunsPage() {
  const { checking: authChecking, user } = useAdminGuard();
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(60);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TaskRunDashboardOut | null>(null);

  useEffect(() => {
    if (user?.role === "admin") {
      void loadData(days, limit);
    }
  }, [user, days, limit]);

  async function loadData(windowDays: number, rowLimit: number) {
    try {
      setLoading(true);
      setError(null);
      const path = withQuery(API_PATHS.admin.taskRuns, {
        days: windowDays,
        limit: rowLimit,
      });
      const response = await apiGet<TaskRunDashboardOut>(path);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const maxDayTotal = useMemo(
    () => Math.max(...(data?.day_series.map((point) => point.total) ?? [0])),
    [data]
  );
  const maxTaskTotal = useMemo(
    () => Math.max(...(data?.task_series.map((point) => point.total) ?? [0])),
    [data]
  );

  if (authChecking || !user) {
    return (
      <div className="container mx-auto max-w-6xl px-4 py-8">
        <div className="text-sm font-medium text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Task Runs</h1>
          <p className="mt-1 text-sm font-medium text-gray-700 dark:text-gray-300">
            Visibility for scheduled Celery tasks and overnight runs.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">Window</label>
            <select
              value={days}
              onChange={(event) => setDays(parseInt(event.target.value, 10))}
              className="rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
            >
              <option value={3}>3 days</option>
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300">Rows</label>
            <select
              value={limit}
              onChange={(event) => setLimit(parseInt(event.target.value, 10))}
              className="rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100"
            >
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={100}>100</option>
              <option value={150}>150</option>
            </select>
          </div>
          <button
            onClick={() => void loadData(days, limit)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 text-sm font-medium text-gray-700 dark:text-gray-300">
          Loading task telemetry...
        </div>
      )}

      {error && (
        <div className="rounded-lg border-2 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 p-4">
          <p className="text-sm font-semibold text-red-900 dark:text-red-300">Failed to load task data</p>
          <p className="mt-1 text-sm text-red-800 dark:text-red-400">{error}</p>
        </div>
      )}

      {data && !loading && !error && (
        <>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border-2 border-slate-300 dark:border-slate-700 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-400">Total Runs</p>
              <p className="mt-1 text-3xl font-bold text-slate-900 dark:text-slate-100">{data.total_runs}</p>
            </div>
            <div className="rounded-xl border-2 border-emerald-300 dark:border-emerald-700 bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950 dark:to-emerald-900/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">Success</p>
              <p className="mt-1 text-3xl font-bold text-emerald-800 dark:text-emerald-200">{data.success_count}</p>
            </div>
            <div className="rounded-xl border-2 border-rose-300 dark:border-rose-700 bg-gradient-to-br from-rose-50 to-rose-100 dark:from-rose-950 dark:to-rose-900/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-700 dark:text-rose-300">Failures</p>
              <p className="mt-1 text-3xl font-bold text-rose-800 dark:text-rose-200">{data.failure_count}</p>
            </div>
            <div className="rounded-xl border-2 border-blue-300 dark:border-blue-700 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900/40 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-300">Success Rate</p>
              <p className="mt-1 text-3xl font-bold text-blue-800 dark:text-blue-200">
                {(data.success_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Daily Status Mix</h2>
              <p className="mt-1 text-xs font-medium text-gray-600 dark:text-gray-400">
                Success, failure, and non-terminal states by day.
              </p>
              <div className="mt-5 space-y-3">
                {data.day_series.length === 0 ? (
                  <p className="text-sm text-gray-600 dark:text-gray-400">No runs in selected window.</p>
                ) : (
                  data.day_series.map((point) => {
                    const successPct = maxDayTotal > 0 ? (point.success / maxDayTotal) * 100 : 0;
                    const failurePct = maxDayTotal > 0 ? (point.failure / maxDayTotal) * 100 : 0;
                    const otherPct = maxDayTotal > 0 ? (point.other / maxDayTotal) * 100 : 0;
                    return (
                      <div key={point.day}>
                        <div className="mb-1 flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                          <span>{point.day}</span>
                          <span>{point.total} run(s)</span>
                        </div>
                        <div className="flex h-3 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                          <div className="bg-emerald-500" style={{ width: `${successPct}%` }} />
                          <div className="bg-rose-500" style={{ width: `${failurePct}%` }} />
                          <div className="bg-slate-400" style={{ width: `${otherPct}%` }} />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Top Task Volume</h2>
              <p className="mt-1 text-xs font-medium text-gray-600 dark:text-gray-400">
                Most active tasks in the current window.
              </p>
              <div className="mt-5 space-y-3">
                {data.task_series.length === 0 ? (
                  <p className="text-sm text-gray-600 dark:text-gray-400">No task runs yet.</p>
                ) : (
                  data.task_series.map((point) => {
                    const totalPct = maxTaskTotal > 0 ? (point.total / maxTaskTotal) * 100 : 0;
                    const failPct = point.total > 0 ? (point.failure / point.total) * 100 : 0;
                    return (
                      <div key={point.task_name} className="space-y-1">
                        <div className="flex items-center justify-between gap-2 text-xs">
                          <span className="truncate font-medium text-gray-800 dark:text-gray-200">
                            {point.task_name}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400">{point.total} total</span>
                        </div>
                        <div className="h-2 rounded-full bg-blue-100 dark:bg-blue-950/40">
                          <div className="h-2 rounded-full bg-blue-500" style={{ width: `${totalPct}%` }} />
                        </div>
                        <p className="text-[11px] text-gray-500 dark:text-gray-400">
                          {(100 - failPct).toFixed(0)}% success · Last {formatDateTime(point.last_run_at)}
                        </p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Recent Runs</h2>
            <p className="mt-1 text-xs font-medium text-gray-600 dark:text-gray-400">
              Latest executions with timing and error details.
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    <th className="px-2 py-2 font-semibold">Task</th>
                    <th className="px-2 py-2 font-semibold">Status</th>
                    <th className="px-2 py-2 font-semibold">Started</th>
                    <th className="px-2 py-2 font-semibold">Duration</th>
                    <th className="px-2 py-2 font-semibold">Worker</th>
                    <th className="px-2 py-2 font-semibold">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_runs.map((run) => (
                    <tr
                      key={run.task_id}
                      className="border-b border-gray-100 dark:border-gray-800 align-top text-gray-800 dark:text-gray-200"
                    >
                      <td className="px-2 py-2">
                        <p className="max-w-[280px] truncate font-medium">{run.task_name}</p>
                        <p className="max-w-[280px] truncate text-xs text-gray-500 dark:text-gray-400">{run.task_id}</p>
                      </td>
                      <td className="px-2 py-2">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                            run.status === "success"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
                              : run.status === "failure"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300"
                                : "bg-slate-100 text-slate-700 dark:bg-slate-700/40 dark:text-slate-300"
                          }`}
                        >
                          {run.status}
                        </span>
                      </td>
                      <td className="px-2 py-2 text-xs">{formatDateTime(run.started_at)}</td>
                      <td className="px-2 py-2 text-xs">{formatDuration(run.runtime_ms)}</td>
                      <td className="px-2 py-2 text-xs">{run.worker_hostname ?? "-"}</td>
                      <td className="px-2 py-2 text-xs text-rose-700 dark:text-rose-300">
                        <p className="max-w-[360px] whitespace-pre-wrap break-words">
                          {run.error ? run.error : "-"}
                        </p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
