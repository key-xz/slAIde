import { useState } from 'react'
import { useSlideGenerator } from './hooks/useSlideGenerator'
import { FileUploadSection } from './components/FileUploadSection'
import { BulkContentUpload } from './components/BulkContentUpload'
import { DownloadSection } from './components/DownloadSection'
import { RulesViewer } from './components/RulesViewer'
import { ErrorDisplay } from './components/ErrorDisplay'

type Tab = 'assets' | 'generate' | 'edit'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('assets')
  
  const {
    file,
    rules,
    loading,
    error,
    generating,
    generatedFile,
    handleFileChange,
    handleUpload,
    handleGenerateDeck,
  } = useSlideGenerator()

  return (
    <div className="app-container">
      <div className="header">
        <h1>slAIde</h1>
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'assets' ? 'active' : ''}`}
            onClick={() => setActiveTab('assets')}
          >
            Asset Upload
          </button>
          <button
            className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
            onClick={() => setActiveTab('generate')}
          >
            Slide Generation
          </button>
          <button
            className={`tab ${activeTab === 'edit' ? 'active' : ''}`}
            onClick={() => setActiveTab('edit')}
          >
            Editing
          </button>
        </div>
      </div>

      <div className="tab-content">
        {activeTab === 'assets' && (
          <div className="assets-tab">
            <h2>Upload Assets & Templates</h2>
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
          <div className="generate-tab">
            <h2>Generate Slide Deck</h2>
            {!rules && (
              <p className="info-message">
                Please upload a PowerPoint template in the Asset Upload tab first.
              </p>
            )}
            
            {rules && (
              <>
                <div className="info-banner">
                  <p>
                    <strong>How it works:</strong> Enter your content below (can be unorganized notes, 
                    bullet points, or paragraphs) and upload any images. Our AI will organize everything 
                    into a professional slide deck using your template layouts.
                  </p>
                </div>
                
                <BulkContentUpload
                  onGenerate={handleGenerateDeck}
                  generating={generating}
                />

                {error && <ErrorDisplay error={error} />}
                {generatedFile && <DownloadSection generatedFile={generatedFile} />}
              </>
            )}
          </div>
        )}

        {activeTab === 'edit' && (
          <div className="edit-tab">
            <h2>Edit Slides</h2>
            <p className="info-message">Editing functionality coming soon...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
