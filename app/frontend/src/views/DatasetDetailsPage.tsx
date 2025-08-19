import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getClaims, getCandidates } from '../lib/api'

interface DatasetDetailsPageProps {
  datasetId: string
  onBack: () => void
}

export function DatasetDetailsPage({ datasetId, onBack }: DatasetDetailsPageProps) {
  const claims = useQuery({ queryKey: ['claims', datasetId], queryFn: () => getClaims(datasetId) })
  const candidates = useQuery({ queryKey: ['candidates', datasetId], queryFn: () => getCandidates(datasetId) })
  
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dataset {datasetId}</h1>
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          ← Back to Datasets
        </button>
      </div>

      <div className="flex items-center gap-3 text-sm text-gray-700">
        <span className="font-medium">Downloads:</span>
        <a className="underline" href="/api/pipeline/download/candidates.json" target="_blank" rel="noreferrer">candidates.json</a>
        <span>•</span>
        <a className="underline" href="/api/pipeline/download/metrics.json" target="_blank" rel="noreferrer">metrics.json</a>
        <span>•</span>
        <a className="underline" href="/api/pipeline/download/rejections.jsonl" target="_blank" rel="noreferrer">rejections.log.jsonl</a>
        <span>•</span>
        <a className="underline" href="/api/pipeline/download/rejections.json" target="_blank" rel="noreferrer">rejections.json</a>
      </div>
      
      <section>
        <h2 className="text-xl font-semibold mb-4">Claims</h2>
        {claims.isLoading && <div>Loading claims...</div>}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-4 text-left font-medium text-gray-900">Claim ID</th>
                <th className="p-4 text-left font-medium text-gray-900">Status</th>
                <th className="p-4 text-left font-medium text-gray-900">Denial Reason</th>
                <th className="p-4 text-left font-medium text-gray-900">Eligible</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {claims.data?.map((c: any) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="p-4 font-medium">{c.claim_id}</td>
                  <td className="p-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      c.status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="p-4">{c.denial_reason || '-'}</td>
                  <td className="p-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      c.eligibility ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {c.eligibility ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-4">Resubmission Candidates</h2>
        {candidates.isLoading && <div>Loading candidates...</div>}
        <div className="bg-white rounded-lg shadow p-6">
          {candidates.data && candidates.data.length > 0 ? (
            <div className="space-y-4">
              {candidates.data.map((r: any) => (
                <div key={r.claim_id} className="border-l-4 border-blue-500 pl-4">
                  <div className="font-medium text-gray-900">Claim ID: {r.claim_id}</div>
                  <div className="text-sm text-gray-600">Reason: {r.resubmission_reason}</div>
                  <div className="text-sm text-gray-600">Recommendation: {r.recommended_changes}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No resubmission candidates found.</p>
          )}
        </div>
      </section>
    </div>
  )
}


