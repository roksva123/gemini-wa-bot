'use client'

import React from 'react'

interface LoadingSkeletonProps {
  count?: number
  height?: string
}

export default function LoadingSkeleton({ count = 1, height = 'h-10' }: LoadingSkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={`skeleton w-full ${height}`} />
      ))}
    </div>
  )
}
