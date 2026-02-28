import { FormEvent, useState } from 'react'

interface ChatInputProps {
  onSubmit: (query: string) => void
  disabled?: boolean
}

export function ChatInput({ onSubmit, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSubmit(input.trim())
      setInput('')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="質問を入力してください（例: 担当のお客様で今注目すべき企業を教えて）"
        disabled={disabled}
        rows={3}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault()
            handleSubmit(e)
          }
        }}
      />
    </form>
  )
}
