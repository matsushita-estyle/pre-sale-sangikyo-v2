import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-md border border-gray-200 p-6',
        className
      )}
    >
      {children}
    </div>
  )
}
