import { useState, useEffect } from 'react'
import type { LayoutRow, Template } from '../types'
import * as templateApi from '../services/templates'

interface LayoutCollectionViewProps {
  onDeleteLayout: (templateId: string, layoutName: string) => void
  onRefresh?: () => void
}

type GroupBy = 'template' | 'category' | 'all'
type SortBy = 'newest' | 'oldest' | 'name'

export function LayoutCollectionView({ onDeleteLayout, onRefresh }: LayoutCollectionViewProps) {
  const [layouts, setLayouts] = useState<Array<LayoutRow & { template: Template }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [groupBy, setGroupBy] = useState<GroupBy>('template')
  const [sortBy, setSortBy] = useState<SortBy>('newest')
  const [searchQuery, setSearchQuery] = useState('')
  const [lastFetch, setLastFetch] = useState<number>(0)

  useEffect(() => {
    // always fetch fresh data when component mounts or remounts
    loadLayouts()
  }, [])

  const loadLayouts = async (forceRefresh = false) => {
    // cache for 30 seconds unless force refresh
    const now = Date.now()
    if (!forceRefresh && lastFetch && (now - lastFetch) < 30000) {
      console.log('using cached layouts (fetched', Math.floor((now - lastFetch) / 1000), 'seconds ago)')
      return
    }
    
    setLoading(true)
    setError(null)
    
    try {
      console.log('fetching latest layouts from database...')
      const allLayouts = await templateApi.getAllUserLayouts()
      setLayouts(allLayouts)
      setLastFetch(Date.now())
      onRefresh?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to load layouts')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteLayout = async (templateId: string, layoutName: string) => {
    if (!confirm(`delete layout "${layoutName}"?`)) {
      return
    }

    try {
      await onDeleteLayout(templateId, layoutName)
      await loadLayouts() // refresh after deletion
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to delete layout')
    }
  }

  // filter layouts based on search query
  const filteredLayouts = layouts.filter(layout => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      layout.name.toLowerCase().includes(query) ||
      layout.category?.toLowerCase().includes(query) ||
      layout.template.name.toLowerCase().includes(query)
    )
  })

  // sort layouts
  const sortedLayouts = [...filteredLayouts].sort((a, b) => {
    switch (sortBy) {
      case 'newest':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      case 'oldest':
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      case 'name':
        return a.name.localeCompare(b.name)
      default:
        return 0
    }
  })

  // group layouts
  const groupedLayouts = (() => {
    if (groupBy === 'all') {
      return { 'all layouts': sortedLayouts }
    }
    
    if (groupBy === 'template') {
      return sortedLayouts.reduce((acc, layout) => {
        const key = layout.template.name
        if (!acc[key]) acc[key] = []
        acc[key].push(layout)
        return acc
      }, {} as Record<string, typeof sortedLayouts>)
    }
    
    if (groupBy === 'category') {
      return sortedLayouts.reduce((acc, layout) => {
        const key = layout.category || 'uncategorized'
        if (!acc[key]) acc[key] = []
        acc[key].push(layout)
        return acc
      }, {} as Record<string, typeof sortedLayouts>)
    }
    
    return {}
  })()

  if (loading) {
    return (
      <div className="my-8 p-8 text-center text-gray-500">
        loading layout collection...
      </div>
    )
  }

  if (error) {
    return (
      <div className="my-8 p-4 bg-red-50 border border-red-200 rounded text-red-800">
        {error}
      </div>
    )
  }

  if (layouts.length === 0) {
    return (
      <div className="my-8 p-8 bg-blue-50 border border-blue-200 rounded-lg text-center">
        <p className="text-gray-700 mb-2">no layouts in your collection yet</p>
        <p className="text-sm text-gray-500">upload a powerpoint template to get started</p>
      </div>
    )
  }

  const totalCount = layouts.length
  const templateCount = new Set(layouts.map(l => l.template_id)).size
  const categoryCount = new Set(layouts.map(l => l.category || 'uncategorized')).size

  return (
    <div className="my-8">
      {/* header with stats */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">layout collection</h3>
          <p className="text-sm text-gray-500 mt-1">
            {totalCount} layouts across {templateCount} templates · {categoryCount} categories
          </p>
        </div>
      </div>

      {/* controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="search layouts, categories, templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value as GroupBy)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="template">group by template</option>
            <option value="category">group by category</option>
            <option value="all">show all</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="newest">newest first</option>
            <option value="oldest">oldest first</option>
            <option value="name">alphabetical</option>
          </select>
        </div>
      </div>

      {/* grouped layouts */}
      {Object.entries(groupedLayouts).map(([groupName, groupLayouts]) => (
        <div key={groupName} className="mb-8">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
            {groupName} ({groupLayouts.length})
          </h4>
          
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
            {groupLayouts.map((layout) => {
              const slideSize = layout.template.slide_size
              const aspectRatio = slideSize.height / slideSize.width
              
              return (
                <div
                  key={layout.id}
                  className="group bg-white border-2 border-gray-200 rounded-lg overflow-hidden transition-all shadow-sm hover:border-blue-400 hover:shadow-md"
                >
                  {/* header */}
                  <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-[10px] font-mono text-gray-900 truncate mb-0.5" title={layout.name}>
                          {layout.name}
                        </div>
                        <div className="text-[8px] text-gray-500 truncate" title={layout.template.name}>
                          from: {layout.template.name}
                        </div>
                        {layout.category && (
                          <div className="text-[8px] text-blue-600 font-medium mt-1">
                            {layout.category}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleDeleteLayout(layout.template_id, layout.name)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-600 p-1 flex-shrink-0"
                        title="delete layout"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  {/* preview */}
                  <div className="p-3">
                    <div
                      className="relative w-full bg-gray-50 border border-gray-100 rounded overflow-hidden mb-2"
                      style={{ paddingBottom: `${aspectRatio * 100}%` }}
                    >
                      <div className="absolute top-0 left-0 w-full h-full">
                        {/* shapes */}
                        {(layout.shapes || []).map((shape: any, sIdx: number) => (
                          <div
                            key={`shape-${sIdx}`}
                            className="absolute border border-gray-200 bg-gray-100/20"
                            style={{
                              left: `${(shape.position.left / slideSize.width) * 100}%`,
                              top: `${(shape.position.top / slideSize.height) * 100}%`,
                              width: `${(shape.position.width / slideSize.width) * 100}%`,
                              height: `${(shape.position.height / slideSize.height) * 100}%`,
                            }}
                          />
                        ))}

                        {/* placeholders */}
                        {layout.placeholders.map((ph: any) => (
                          <div
                            key={ph.idx}
                            className={`absolute border flex items-center justify-center text-[6px] font-bold rounded-sm ${
                              ph.type === 'text'
                                ? 'border-blue-200 bg-blue-50/40 text-blue-400'
                                : 'border-amber-200 bg-amber-50/40 text-amber-400'
                            }`}
                            style={{
                              left: `${(ph.position.left / slideSize.width) * 100}%`,
                              top: `${(ph.position.top / slideSize.height) * 100}%`,
                              width: `${(ph.position.width / slideSize.width) * 100}%`,
                              height: `${(ph.position.height / slideSize.height) * 100}%`,
                            }}
                          >
                            {ph.type === 'text' ? 'T' : 'IMG'}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* placeholder badges */}
                    <div className="flex flex-wrap gap-1">
                      {layout.placeholders.map((ph: any) => (
                        <span
                          key={ph.idx}
                          className="px-1 py-0.5 bg-gray-100 text-gray-500 rounded text-[7px] font-medium uppercase tracking-tight"
                        >
                          {ph.type}
                        </span>
                      ))}
                      {layout.placeholders.length === 0 && (
                        <span className="text-[7px] text-gray-300 italic">no placeholders</span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {filteredLayouts.length === 0 && searchQuery && (
        <div className="py-12 text-center text-gray-500">
          <p>no layouts match "{searchQuery}"</p>
          <button
            onClick={() => setSearchQuery('')}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            clear search
          </button>
        </div>
      )}
    </div>
  )
}
