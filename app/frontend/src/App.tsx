import React, { useState } from 'react'
import { UploadPage } from './views/UploadPage'
import { DatasetsPage } from './views/DatasetsPage'
import { DatasetDetailsPage } from './views/DatasetDetailsPage'

type View = 'upload' | 'datasets' | 'dataset-details'

export function App() {
  const [currentView, setCurrentView] = useState<View>('upload')
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null)

  const handleViewDatasets = () => setCurrentView('datasets')
  const handleViewUpload = () => setCurrentView('upload')
  const handleViewDatasetDetails = (id: number) => {
    setSelectedDatasetId(id)
    setCurrentView('dataset-details')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">Claims Pipeline</h1>
            <div className="space-x-4">
              <button
                onClick={handleViewUpload}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  currentView === 'upload'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Upload
              </button>
              <button
                onClick={handleViewDatasets}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  currentView === 'datasets'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Datasets
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main>
        {currentView === 'upload' && <UploadPage />}
        {currentView === 'datasets' && (
          <DatasetsPage onViewDataset={handleViewDatasetDetails} />
        )}
        {currentView === 'dataset-details' && selectedDatasetId && (
          <DatasetDetailsPage
            datasetId={selectedDatasetId}
            onBack={handleViewDatasets}
          />
        )}
      </main>
    </div>
  )
}

