import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { listDatasets } from '../lib/api'

interface DatasetsPageProps {
  onViewDataset: (id: string) => void
}

export function DatasetsPage({ onViewDataset }: DatasetsPageProps) {
  const { data, isLoading } = useQuery({ queryKey: ['datasets'], queryFn: listDatasets })
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Datasets</h1>
      {isLoading && <div>Loading...</div>}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-4 font-medium text-gray-900">ID</th>
              <th className="text-left p-4 font-medium text-gray-900">Filename</th>
              <th className="text-left p-4 font-medium text-gray-900">Source</th>
              <th className="text-left p-4 font-medium text-gray-900">Records</th>
              <th className="text-left p-4 font-medium text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data?.map((d) => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="p-4">{d.id}</td>
                <td className="p-4">{d.filename}</td>
                <td className="p-4">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                    {d.source_system}
                  </span>
                </td>
                <td className="p-4">{d.record_count}</td>
                <td className="p-4">
                  <button
                    onClick={() => onViewDataset(d.id)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


