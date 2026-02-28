import { marked } from 'marked'
import { useMemo } from 'react'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

// markedの設定
marked.setOptions({
  breaks: true, // 改行を<br>に変換
  gfm: true, // GitHub Flavored Markdown
})

export function ChatMessage({ role, content }: ChatMessageProps) {
  const html = useMemo(() => {
    if (role === 'assistant') {
      return marked.parse(content) as string
    }
    return content
  }, [role, content])

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
      <div className="max-w-[90%] [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:mt-6 [&_h2]:mb-4 [&_h2]:text-gray-800 [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:mt-5 [&_h3]:mb-3 [&_h3]:text-gray-800 [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:my-4 [&_li]:my-1 [&_li]:leading-7 [&_strong]:font-semibold [&_strong]:text-gray-900 [&_p]:my-3 [&_p]:leading-7">
        <div
          dangerouslySetInnerHTML={{ __html: html as string }}
        />
      </div>
    </div>
  )
}
