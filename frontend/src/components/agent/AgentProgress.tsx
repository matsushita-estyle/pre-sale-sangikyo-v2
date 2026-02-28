import { ProgressEvent } from '@/types/agent'
import { CheckCircle, Loader2 } from 'lucide-react'

interface AgentProgressProps {
  events: ProgressEvent[]
  currentMessage: string
}

export function AgentProgress({ events, currentMessage }: AgentProgressProps) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
      {/* 現在の進捗メッセージ */}
      {currentMessage && (
        <div className="flex items-center space-x-2 text-gray-700">
          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          <span className="text-sm font-medium">{currentMessage}</span>
        </div>
      )}

      {/* 進捗履歴 */}
      {events.length > 0 && (
        <div className="space-y-1.5 border-t border-gray-200 pt-3">
          {events.map((event, idx) => (
            <ProgressEventItem key={idx} event={event} />
          ))}
        </div>
      )}
    </div>
  )
}

function ProgressEventItem({ event }: { event: ProgressEvent }) {
  switch (event.type) {
    case 'function_call':
      return (
        <div className="flex items-start space-x-2">
          <Loader2 className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0 animate-spin" />
          <div className="text-xs text-gray-600">
            <span className="font-medium">{event.tool_name}</span>を実行中
            {event.arguments && (
              <span className="text-gray-500 ml-1">
                (
                {Object.entries(event.arguments)
                  .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                  .join(', ')}
                )
              </span>
            )}
          </div>
        </div>
      )

    case 'function_result':
      return (
        <div className="flex items-start space-x-2">
          <CheckCircle className="w-3 h-3 text-gray-500 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-gray-700">{event.result}</div>
        </div>
      )

    case 'thinking':
      return (
        <div className="flex items-start space-x-2">
          <Loader2 className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0 animate-spin" />
          <div className="text-xs text-gray-500 italic">{event.message}</div>
        </div>
      )

    case 'error':
      return (
        <div className="flex items-start space-x-2">
          <span className="text-red-500 text-xs mt-0.5">✗</span>
          <div className="text-xs text-red-600">{event.message}</div>
        </div>
      )

    default:
      return null
  }
}
