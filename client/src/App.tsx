import { useState } from 'react'
import { useSlideGenerator } from './hooks/useSlideGenerator'
import { FileUploadSection } from './components/FileUploadSection'
import { BulkContentUpload } from './components/BulkContentUpload'
import { ContentStructurePreview } from './components/ContentStructurePreview'
import { SlideEditor } from './components/SlideEditor'
import { DownloadSection } from './components/DownloadSection'
import { RulesViewer } from './components/RulesViewer'
import { ErrorDisplay } from './components/ErrorDisplay'

type Tab = 'assets' | 'generate'

function App() {
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
    handleFileChange,
    handleUpload,
    handlePreprocessContent,
    handleGenerateFromStructure,
    handleGeneratePreview,
    handleGenerateDeck,
    setSlides,
    setContentStructure,
  } = useSlideGenerator()

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <div className="flex-shrink-0 bg-gray-50 border-b border-gray-200">
        <h1 className="px-8 pt-4 pb-2 text-2xl font-semibold">slAIde</h1>
        <div className="flex px-8">
          <button
            className={`px-6 py-3 font-medium text-sm transition-all border-b-2 ${
              activeTab === 'assets'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-black/5'
            }`}
            onClick={() => setActiveTab('assets')}
          >
            Template Upload
          </button>
          <button
            className={`px-6 py-3 font-medium text-sm transition-all border-b-2 ${
              activeTab === 'generate'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-black/5'
            }`}
            onClick={() => setActiveTab('generate')}
          >
            Slide Generation
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {activeTab === 'assets' && (
          <div className="max-w-6xl mx-auto">
            <h2 className="text-xl font-semibold mb-6">Upload Template</h2>
            <FileUploadSection
              file={file}
              loading={loading}
              onFileChange={handleFileChange}
              onUpload={handleUpload}
            />
            {error && <ErrorDisplay error={error} />}
            {rules && <RulesViewer rules={rules} />}
          </div>
        )}

        {activeTab === 'generate' && (
          <div className="max-w-6xl mx-auto">
            {!rules ? (
              <p className="p-4 bg-blue-50 border border-blue-200 rounded text-blue-800 my-4">
                Please upload a template first.
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
                      onEdit={(editedStructure) => {
                        setContentStructure(editedStructure)
                      }}
                      loading={previewLoading}
                    />
                    <button
                      onClick={() => setContentStructure(null)}
                      className="mt-4 px-4 py-2 text-gray-400 hover:text-gray-600 underline text-sm"
                    >
                      ← Back
                    </button>
                  </>
                )}
                
                {slides.length > 0 && rules && (
                  <SlideEditor
                    slides={slides}
                    rules={rules}
                    onSlidesUpdate={setSlides}
                    onGenerate={handleGenerateDeck}
                    generating={generating}
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
