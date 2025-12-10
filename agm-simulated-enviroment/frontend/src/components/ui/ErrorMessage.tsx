import { AlertCircle } from 'lucide-react'

interface ErrorMessageProps {
  message: string
  actionSuggestion?: string
}

export function ErrorMessage({ message, actionSuggestion }: ErrorMessageProps) {
  return (
    <div className="p-3 bg-red-50 border border-red-200 rounded-md">
      <p className="text-sm text-red-600 flex items-center gap-2">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        {message}
      </p>
      {actionSuggestion && (
        <p className="text-sm text-red-500 mt-2 ml-6">
          💡 {actionSuggestion}
        </p>
      )}
    </div>
  )
}

