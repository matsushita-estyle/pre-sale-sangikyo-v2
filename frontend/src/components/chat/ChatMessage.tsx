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
          className="prose prose-sm max-w-none text-gray-800 leading-relaxed
            prose-headings:font-semibold prose-headings:text-gray-900
            prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
            prose-p:my-3 prose-p:leading-7
            prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6
            prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6
            prose-li:my-1 prose-li:leading-7
            prose-strong:font-semibold prose-strong:text-gray-900
            prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono prose-code:text-gray-800
            prose-pre:bg-gray-100 prose-pre:border prose-pre:border-gray-200 prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto
            prose-a:text-blue-600 prose-a:underline hover:prose-a:text-blue-700
            prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-700"
          dangerouslySetInnerHTML={{ __html: html as string }}
        />
      </div>
    </div>
  )
}
