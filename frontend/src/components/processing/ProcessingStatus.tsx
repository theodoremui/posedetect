'use client'

import React, { useState, useEffect } from 'react'
import { Activity, Clock, CheckCircle, AlertCircle, X } from 'lucide-react'
import { getProcessingJobs, cancelProcessing } from '@/lib/api'
import { ProcessingJob } from '@/lib/api'

export function ProcessingStatus() {
  const [jobs, setJobs] = useState<ProcessingJob[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
    
    // Refresh every 5 seconds
    const interval = setInterval(fetchJobs, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchJobs = async () => {
    try {
      const data = await getProcessingJobs()
      setJobs(data)
    } catch (error) {
      console.error('Failed to fetch processing jobs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await cancelProcessing(id)
      fetchJobs()
    } catch (error) {
      console.error('Failed to cancel processing:', error)
    }
  }

  const getStatusIcon = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'processing':
        return <Activity className="w-5 h-5 text-blue-500 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />
    }
  }

  const getStatusColor = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'pending':
        return 'status-pending'
      case 'processing':
        return 'status-processing'
      case 'completed':
        return 'status-completed'
      case 'error':
        return 'status-error'
    }
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading processing jobs...</div>
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No processing jobs</h3>
        <p className="text-gray-600">Start processing some files to see jobs here</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Processing Status</h2>
      <div className="space-y-4">
        {jobs.map((job) => (
          <div key={job.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {getStatusIcon(job.status)}
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Job #{job.id.slice(0, 8)}
                  </p>
                  <p className="text-xs text-gray-500">
                    File ID: {job.file_id}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className={`status-badge ${getStatusColor(job.status)}`}>
                  {job.status}
                </span>
                
                {job.status === 'processing' && (
                  <button
                    onClick={() => handleCancel(job.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors duration-200"
                    title="Cancel"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            
            {job.status === 'processing' && (
              <div className="mb-3">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">Progress</span>
                  <span className="text-gray-900 font-medium">{job.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>
            )}
            
            <div className="text-xs text-gray-500 space-y-1">
              {job.started_at && (
                <p>Started: {new Date(job.started_at).toLocaleString()}</p>
              )}
              {job.completed_at && (
                <p>Completed: {new Date(job.completed_at).toLocaleString()}</p>
              )}
              {job.error_message && (
                <p className="text-red-600">Error: {job.error_message}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 