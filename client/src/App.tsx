import { useState } from 'react'
import { useSlideGenerator } from './hooks/useSlideGenerator'
import { FileUploadSection } from './components/FileUploadSection'
import { BulkContentUpload } from './components/BulkContentUpload'
import { ContentStructurePreview } from './components/ContentStructurePreview'
import { SlideEditor } from './components/SlideEditor'
import { DownloadSection } from './components/DownloadSection'
import { LayoutManager } from './components/LayoutManager'
import { TemplateSelector } from './components/TemplateSelector'
import { LayoutCollectionView } from './components/LayoutCollectionView'
import { ErrorDisplay } from './components/ErrorDisplay'
import { UserMenu } from './components/UserMenu'
import { useAuth } from './contexts/AuthContext'

type Tab = 'assets' | 'collection' | 'generate'

function App() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<Tab>('assets')
  
  const {
    file,
    rules,
    loading,
    error,
    generating,
    generatedFile,
    slides,
    previewLoading,
    contentStructure,
    preprocessing,
    regeneratingSlideId,
    templates,
    currentTemplateId,
    handleFileChange,
    handleUpload,
    handlePreprocessContent,
    handleGenerateFromStructure,
    handleGenerateDeck,
    handleDeleteLayout,
    handleDeleteLayoutFromCollection,
    handleDeleteTemplate,
    handleRegenerateSlide,
    loadTemplate,
    loadTemplates,
    setSlides,
    setRules,
    setContentStructure,
  } = useSlideGenerator()

  const currentTemplate = currentTemplateId
    ? templates.find((t) => t.id === currentTemplateId) || null
    : null

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <div className="flex-shrink-0 bg-gray-50 border-b border-gray-200">
        <div className="px-8 pt-4 pb-2 flex justify-between items-center">
          <h1 className="text-2xl font-semibold">slAIde</h1>
          <UserMenu />
        </div>
        <div className="flex px-8">
          <button
            className={`px-6 py-3 font-medium text-sm transition-all border-b-2 ${
              activeTab === 'assets'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-black/5'
            }`}
            onClick={() => setActiveTab('assets')}
          >
            template upload
          </button>
          {user && (
            <button
              className={`px-6 py-3 font-medium text-sm transition-all border-b-2 ${
                activeTab === 'collection'
                  ? 'text-blue-600 border-blue-600'
                  : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-black/5'
              }`}
              onClick={() => setActiveTab('collection')}
            >
              layout collection
            </button>
          )}
          <button
            className={`px-6 py-3 font-medium text-sm transition-all border-b-2 ${
              activeTab === 'generate'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-black/5'
            }`}
            onClick={() => setActiveTab('generate')}
          >
            slide generation
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {activeTab === 'assets' && (
          <div className="max-w-6xl mx-auto">
            {user && templates.length > 0 && (
              <TemplateSelector
                templates={templates}
                currentTemplateId={currentTemplateId}
                onSelectTemplate={loadTemplate}
                onDeleteTemplate={handleDeleteTemplate}
                loading={loading}
              />
            )}
            
            <h2 className="text-xl font-semibold mb-6">
              {user && templates.length > 0 ? 'upload new template' : 'upload template'}
            </h2>
            <FileUploadSection
              file={file}
              loading={loading}
              onFileChange={handleFileChange}
              onUpload={handleUpload}
            />
            {error && <ErrorDisplay error={error} />}
            {rules && <LayoutManager rules={rules} onDeleteLayout={handleDeleteLayout} />}
          </div>
        )}

        {activeTab === 'collection' && (
          <div className="max-w-7xl mx-auto">
            {user ? (
              <LayoutCollectionView
                onDeleteLayout={handleDeleteLayoutFromCollection}
                onRefresh={loadTemplates}
              />
            ) : (
              <div className="p-8 bg-blue-50 border border-blue-200 rounded-lg text-center">
                <p className="text-gray-700">please log in to view your layout collection</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'generate' && (
          <div className="max-w-6xl mx-auto">
            {user && templates.length > 0 && (
              <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex-1 min-w-[220px]">
                    <div className="text-xs font-semibold text-gray-600 mb-1">template group</div>
                    <select
                      value={currentTemplateId || ''}
                      onChange={(e) => {
                        const nextId = e.target.value
                        if (nextId) loadTemplate(nextId)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="" disabled>
                        select a template…
                      </option>
                      {templates.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}
                        </option>
                      ))}
                    </select>
                    {currentTemplate && (
                      <div className="mt-1 text-[11px] text-gray-500">
                        using: {currentTemplate.name} · {currentTemplate.slide_size?.width}x{currentTemplate.slide_size?.height}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => setActiveTab('assets')}
                    className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
                  >
                    upload more templates
                  </button>
                </div>
              </div>
            )}

            {!rules ? (
              <p className="p-4 bg-blue-50 border border-blue-200 rounded text-blue-800 my-4">
                {user && templates.length > 0
                  ? 'please select a template group above.'
                  : 'please upload a template first.'}
              </p>
            ) : (
              <>
                {!contentStructure && (
                  <BulkContentUpload
                    onPreprocess={handlePreprocessContent}
                    preprocessing={preprocessing}
                  />
                )}

                {error && <ErrorDisplay error={error} />}
                
                {contentStructure && !slides.length && (
                  <>
                    <ContentStructurePreview
                      structure={contentStructure}
                      onApprove={handleGenerateFromStructure}
                      onEdit={(editedStructure: any) => {
                        setContentStructure(editedStructure)
                      }}
                      loading={previewLoading}
                    />
                    <button
                      onClick={() => setContentStructure(null)}
                      className="mt-4 px-4 py-2 text-gray-400 hover:text-gray-600 underline text-sm"
                    >
                      ← back
                    </button>
                  </>
                )}
                
                {slides.length > 0 && rules && (
                  <SlideEditor
                    slides={slides}
                    rules={rules}
                    onSlidesUpdate={setSlides}
                    onRulesUpdate={setRules}
                    onGenerate={handleGenerateDeck}
                    onRegenerateSlide={handleRegenerateSlide}
                    generating={generating}
                    regeneratingSlideId={regeneratingSlideId}
                  />
                )}

                {generatedFile && <DownloadSection generatedFile={generatedFile} />}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
