'use client'

import React, { useState } from 'react'
import { FileUpload } from '@/components/upload/FileUpload'
import { FileManager } from '@/components/files/FileManager'
import { ProcessingStatus } from '@/components/processing/ProcessingStatus'
import { Stats } from '@/components/dashboard/Stats'

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<'upload' | 'files' | 'processing'>('upload')

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          PoseDetect AI
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Advanced pose detection and analysis for videos and images using state-of-the-art AI technology
        </p>
      </div>

      {/* Stats Dashboard */}
      <Stats />

      {/* Navigation Tabs */}
      <div className="flex justify-center">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow-sm border border-gray-200">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-6 py-2 rounded-md font-medium transition-colors duration-200 ${
              activeTab === 'upload'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            Upload Files
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`px-6 py-2 rounded-md font-medium transition-colors duration-200 ${
              activeTab === 'files'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            File Manager
          </button>
          <button
            onClick={() => setActiveTab('processing')}
            className={`px-6 py-2 rounded-md font-medium transition-colors duration-200 ${
              activeTab === 'processing'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            Processing Status
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'upload' && <FileUpload />}
        {activeTab === 'files' && <FileManager />}
        {activeTab === 'processing' && <ProcessingStatus />}
      </div>
    </div>
  )
} 