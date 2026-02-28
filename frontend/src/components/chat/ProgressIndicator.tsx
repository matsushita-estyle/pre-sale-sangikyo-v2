import { Loader2 } from 'lucide-react'
import { Card } from '@/components/shared/Card'
import { StreamEvent } from '@/types/agent'

interface ProgressIndicatorProps {
  events: StreamEvent[]
  isStreaming: boolean
}

export function ProgressIndicator({
  events,
  isStreaming,
}: ProgressIndicatorProps) {
  if (!isStreaming && events.length === 0) return null

  return (
    <Card className="bg-gray-50 border-gray-300">
      <div className="flex items-start gap-3">
        {isStreaming && <Loader2 className="w-5 h-5 animate-spin text-blue-600" />}
        <div className="flex-1 space-y-2">
          <h3 className="font-semibold text-gray-900">処理状況</h3>
          <div className="space-y-1 text-sm text-gray-700">
            {events.map((event, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <span className="text-gray-400">•</span>
                <span>{event.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
