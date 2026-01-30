import { useState, useEffect } from 'react'

interface LoadingIndicatorProps {
  stage: 'preprocessing' | 'generating' | 'compressing'
  detail?: string
}

export function LoadingIndicator({ stage, detail }: LoadingIndicatorProps) {
  const [elapsed, setElapsed] = useState(0)
  const [dots, setDots] = useState('')

  useEffect(() => {
    const startTime = Date.now()
    
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const dotsTimer = setInterval(() => {
      setDots(prev => (prev.length >= 3 ? '' : prev + '.'))
    }, 500)

    return () => clearInterval(dotsTimer)
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  const getStageInfo = () => {
    switch (stage) {
      case 'preprocessing':
        return {
          title: 'analyzing content',
          description: 'AI is analyzing your content and organizing it into slides',
          icon: '🔍',
          colorClass: 'bg-gradient-to-r from-blue-500 to-blue-600'
        }
      case 'generating':
        return {
          title: 'generating presentation',
          description: 'creating slides with your content and layouts',
          icon: '✨',
          colorClass: 'bg-gradient-to-r from-green-500 to-green-600'
        }
      case 'compressing':
        return {
          title: 'compressing content',
          description: 'optimizing text to fit within slide boundaries',
          icon: '🔄',
          colorClass: 'bg-gradient-to-r from-purple-500 to-purple-600'
        }
    }
  }

  const stageInfo = getStageInfo()
  const progress = Math.min((elapsed / 120) * 100, 95) // cap at 95% until done

  return (
    <div className="my-8 p-8 bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-300 rounded-xl shadow-lg">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="text-4xl animate-pulse">{stageInfo.icon}</div>
            <div>
              <h3 className="text-xl font-bold text-gray-800">{stageInfo.title}{dots}</h3>
              <p className="text-sm text-gray-600 mt-1">{stageInfo.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-mono font-bold text-gray-700">{formatTime(elapsed)}</div>
            <div className="text-xs text-gray-500 mt-1">elapsed time</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className={`h-full ${stageInfo.colorClass} transition-all duration-1000 ease-out relative overflow-hidden`}
              style={{ width: `${progress}%` }}
            >
              {/* Animated shine effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>in progress</span>
            <span>{Math.floor(progress)}%</span>
          </div>
        </div>

        {/* Detail */}
        {detail && (
          <div className="p-3 bg-white border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-700">{detail}</p>
          </div>
        )}

        {/* Status Messages */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">processing your request</p>
              <p className="text-xs text-blue-700 mt-1">
                {elapsed < 30 && "this typically takes 30-60 seconds"}
                {elapsed >= 30 && elapsed < 90 && "processing complex content may take 1-2 minutes"}
                {elapsed >= 90 && elapsed < 150 && "still working... large requests can take up to 3 minutes"}
                {elapsed >= 150 && "this is taking longer than expected, but still processing..."}
              </p>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  )
}
