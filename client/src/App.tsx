import { useSlideGenerator } from './hooks/useSlideGenerator'
import { FileUploadSection } from './components/FileUploadSection'
import { LayoutSelector } from './components/LayoutSelector'
import { PlaceholderForm } from './components/PlaceholderForm'
import { DownloadSection } from './components/DownloadSection'
import { RulesViewer } from './components/RulesViewer'
import { ErrorDisplay } from './components/ErrorDisplay'

function App() {
  const {
    file,
    rules,
    loading,
    error,
    selectedLayout,
    inputs,
    generating,
    generatedFile,
    handleFileChange,
    handleUpload,
    handleLayoutSelect,
    handleTextInput,
    handleImageInput,
    handleGenerateSlide,
  } = useSlideGenerator()

  return (
    <div className="app-container">
      <h1>slAIde</h1>
      
      <FileUploadSection
        file={file}
        loading={loading}
        onFileChange={handleFileChange}
        onUpload={handleUpload}
      />

      {error && <ErrorDisplay error={error} />}

      {rules && rules.layouts && (
        <LayoutSelector
          layouts={rules.layouts}
          onLayoutSelect={handleLayoutSelect}
        />
      )}

      {selectedLayout && (
        <PlaceholderForm
          layout={selectedLayout}
          inputs={inputs}
          generating={generating}
          onTextInput={handleTextInput}
          onImageInput={handleImageInput}
          onGenerate={handleGenerateSlide}
        />
      )}

      {generatedFile && <DownloadSection generatedFile={generatedFile} />}

      {rules && <RulesViewer rules={rules} />}
    </div>
  )
}

export default App
