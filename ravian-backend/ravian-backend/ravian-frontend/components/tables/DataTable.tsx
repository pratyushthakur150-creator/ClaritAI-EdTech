'use client'

import React from 'react'
import { Inbox } from 'lucide-react'

export interface Column<T> {
  key: string
  header: string
  render?: (item: T) => React.ReactNode
  className?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (item: T) => string
  emptyMessage?: string
  emptyIcon?: React.ReactNode
  isLoading?: boolean
  loadingNode?: React.ReactNode
  /** Number of skeleton rows to show while loading (default: 5) */
  skeletonRows?: number
}

/** Skeleton row component for loading state */
function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="border-b border-slate-100 animate-pulse">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-4">
          <div className="skeleton skeleton-text" style={{ width: `${50 + Math.random() * 30}%` }} />
        </td>
      ))}
    </tr>
  )
}

export default function DataTable<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No data found',
  emptyIcon,
  isLoading,
  loadingNode,
  skeletonRows = 5,
}: DataTableProps<T>) {
  // Custom loading node override
  if (isLoading && loadingNode) {
    return <>{loadingNode}</>
  }

  // Skeleton loading state
  if (isLoading) {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full" aria-busy="true" aria-label="Loading data">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={`table-header ${col.className ?? ''}`}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white">
            {Array.from({ length: skeletonRows }).map((_, i) => (
              <SkeletonRow key={i} columns={columns.length} />
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-400">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
          {emptyIcon || <Inbox className="w-7 h-7 text-slate-300" />}
        </div>
        <p className="text-sm font-medium text-slate-500">{emptyMessage}</p>
        <p className="text-xs text-slate-400 mt-1">Try adjusting your filters or adding new data</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full" aria-label="Data table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`table-header ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-100">
          {data.map((item, rowIdx) => (
            <tr
              key={keyExtractor(item)}
              className="table-row animate-fade-in-up"
              style={{ animationDelay: `${rowIdx * 0.03}s` }}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`table-cell ${col.className ?? ''}`}
                >
                  {col.render
                    ? col.render(item)
                    : String((item as Record<string, unknown>)[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
