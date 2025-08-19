import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { runPipeline } from '../lib/api'

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [source, setSource] = useState<string>('')
  const queryClient = useQueryClient()
  
  const mutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected')
      return runPipeline(file)
    },
    onSuccess: () => {
      // Invalidate datasets query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      setFile(null)
      setSource('')
    },
  })

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-semibold mb-6">Upload Dataset</h1>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File
            </label>
            <input
              type="file"
              accept=".csv,.json"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source System
            </label>
            <select
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              <option value="">Auto-detect</option>
              <option value="alpha">Alpha (CSV)</option>
              <option value="beta">Beta (JSON)</option>
            </select>
          </div>
          
          <button
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            onClick={() => mutation.mutate()}
            disabled={!file || mutation.isPending}
          >
            {mutation.isPending ? 'Processing...' : 'Upload & Run Pipeline'}
          </button>
          
          {mutation.isSuccess && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md space-y-2">
              <p className="text-green-800">Pipeline completed successfully!</p>
              { (mutation as any).data?.metrics && (
                <pre className="text-xs bg-white p-2 rounded border overflow-auto">{JSON.stringify((mutation as any).data.metrics, null, 2)}</pre>
              )}
              <div className="text-sm text-gray-700">
                <a className="underline" href="/api/pipeline/download/candidates.json" target="_blank" rel="noreferrer">Download candidates.json</a>
                <span className="mx-2">|</span>
                <a className="underline" href="/api/pipeline/download/metrics.json" target="_blank" rel="noreferrer">Download metrics.json</a>
                <span className="mx-2">|</span>
                <a className="underline" href="/api/pipeline/download/rejections.jsonl" target="_blank" rel="noreferrer">Download rejections.log.jsonl</a>
                <span className="mx-2">|</span>
                <a className="underline" href="/api/pipeline/download/rejections.json" target="_blank" rel="noreferrer">Download rejections.json</a>
              </div>
            </div>
          )}
          
          {mutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800">Error: {(mutation.error as Error).message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


