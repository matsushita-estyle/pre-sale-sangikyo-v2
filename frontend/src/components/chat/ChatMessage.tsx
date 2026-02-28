import { marked } from 'marked'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const html = role === 'assistant' ? marked(content) : content

  if (role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-blue-100 text-gray-900 px-4 py-2 rounded-2xl max-w-[80%] break-words">
          <p className="whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[90%]">
        <div
          className="prose prose-sm max-w-none text-gray-800 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: html as string }}
        />
      </div>
    </div>
  )
}
