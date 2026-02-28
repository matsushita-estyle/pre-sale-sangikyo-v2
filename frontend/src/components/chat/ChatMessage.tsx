import { marked } from 'marked'
import { Card } from '@/components/shared/Card'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const html = role === 'assistant' ? marked(content) : content

  return (
    <Card
      className={
        role === 'user'
          ? 'bg-blue-50 border-blue-200'
          : 'bg-white border-gray-200'
      }
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            role === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-600 text-white'
          }`}
        >
          {role === 'user' ? 'あ' : 'AI'}
        </div>
        <div className="flex-1 min-w-0">
          {role === 'assistant' ? (
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: html as string }}
            />
          ) : (
            <p className="text-gray-900 whitespace-pre-wrap">{content}</p>
          )}
        </div>
      </div>
    </Card>
  )
}
