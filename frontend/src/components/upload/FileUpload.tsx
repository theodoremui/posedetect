'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, File, Globe, AlertCircle, CheckCircle } from 'lucide-react'
import { uploadFile, uploadFromUrl } from '@/lib/api'

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

export function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [urlInput, setUrlInput] = useState('')
  const [isUrlUploading, setIsUrlUploading] = useState(false)
  const [uploadMode, setUploadMode] = useState<'files' | 'url'>('files')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
    }))

    setFiles(prev => [...prev, ...newFiles])

    // Upload files
    for (const file of acceptedFiles) {
      const fileId = newFiles.find(f => f.name === file.name)?.id
      if (!fileId) continue

      try {
        await uploadFile(file, (progress) => {
          setFiles(prev => prev.map(f => 
            f.id === fileId ? { ...f, progress } : f
          ))
        })

        setFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'success', progress: 100 } : f
        ))
      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error', 
            error: error instanceof Error ? error.message : 'Upload failed' 
          } : f
        ))
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    },
    maxSize: 500 * 1024 * 1024, // 500MB
  })

  const handleUrlUpload = async () => {
    if (!urlInput.trim()) return

    setIsUrlUploading(true)
    try {
      await uploadFromUrl(urlInput)
      setUrlInput('')
      // Add success notification
    } catch (error) {
      console.error('URL upload failed:', error)
      // Add error notification
    } finally {
      setIsUrlUploading(false)
    }
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Upload Mode Selector */}
      <div className="flex justify-center">
        <div className="flex bg-white rounded-lg border border-gray-200 p-1">
          <button
            onClick={() => setUploadMode('files')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors duration-200 ${
              uploadMode === 'files'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <File className="w-4 h-4" />
            <span>Upload Files</span>
          </button>
          <button
            onClick={() => setUploadMode('url')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors duration-200 ${
              uploadMode === 'url'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>From URL</span>
          </button>
        </div>
      </div>

      {/* File Upload */}
      {uploadMode === 'files' && (
        <div className="card">
          <div
            {...getRootProps()}
            className={`upload-zone ${isDragActive ? 'active' : ''}`}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-gray-600 mb-4">
              or click to select files
            </p>
            <p className="text-sm text-gray-500">
              Supports videos (MP4, AVI, MOV, MKV, WebM) and images (JPG, PNG, GIF, BMP, WebP)
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Maximum file size: 500MB
            </p>
          </div>
        </div>
      )}

      {/* URL Upload */}
      {uploadMode === 'url' && (
        <div className="card">
          <div className="text-center">
            <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Upload from URL
            </h3>
            <div className="max-w-md mx-auto">
              <div className="flex space-x-2">
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://example.com/video.mp4"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button
                  onClick={handleUrlUpload}
                  disabled={!urlInput.trim() || isUrlUploading}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUrlUploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Uploaded Files</h3>
          <div className="space-y-3">
            {files.map((file) => (
              <div key={file.id} className="file-item">
                <div className="flex items-center space-x-3 flex-1">
                  <File className="w-5 h-5 text-gray-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {file.status === 'uploading' && (
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{file.progress}%</span>
                    </div>
                  )}
                  
                  {file.status === 'success' && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  
                  {file.status === 'error' && (
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-red-500" />
                      <span className="text-xs text-red-600">{file.error}</span>
                    </div>
                  )}
                  
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors duration-200"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 