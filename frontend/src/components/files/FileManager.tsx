'use client'

import React, { useState, useEffect } from 'react'
import { FileText, Download, Trash2, Edit2, Play } from 'lucide-react'
import { getFiles, deleteFile, renameFile, startProcessing } from '@/lib/api'
import { FileItem } from '@/lib/api'

export function FileManager() {
  const [files, setFiles] = useState<FileItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingFile, setEditingFile] = useState<string | null>(null)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      const data = await getFiles()
      setFiles(data)
    } catch (error) {
      console.error('Failed to fetch files:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this file?')) {
      try {
        await deleteFile(id)
        setFiles(prev => prev.filter(f => f.id !== id))
      } catch (error) {
        console.error('Failed to delete file:', error)
      }
    }
  }

  const handleRename = async (id: string) => {
    if (!newName.trim()) return
    
    try {
      const updatedFile = await renameFile(id, newName)
      setFiles(prev => prev.map(f => f.id === id ? updatedFile : f))
      setEditingFile(null)
      setNewName('')
    } catch (error) {
      console.error('Failed to rename file:', error)
    }
  }

  const handleProcess = async (id: string) => {
    try {
      await startProcessing(id)
      // Refresh files to show updated status
      fetchFiles()
    } catch (error) {
      console.error('Failed to start processing:', error)
    }
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading files...</div>
  }

  if (files.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No files uploaded</h3>
        <p className="text-gray-600">Upload some files to get started</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">File Manager</h2>
      <div className="space-y-4">
        {files.map((file) => (
          <div key={file.id} className="file-item">
            <div className="flex items-center space-x-3 flex-1">
              <FileText className="w-5 h-5 text-gray-400" />
              <div className="flex-1 min-w-0">
                {editingFile === file.id ? (
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onBlur={() => handleRename(file.id)}
                    onKeyPress={(e) => e.key === 'Enter' && handleRename(file.id)}
                    className="text-sm font-medium text-gray-900 bg-transparent border-b border-primary-500 focus:outline-none"
                    autoFocus
                  />
                ) : (
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                )}
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>Size: {Math.round(file.size / 1024)} KB</span>
                  <span>Status: {file.status}</span>
                  <span>Uploaded: {new Date(file.upload_date).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setEditingFile(file.id)
                  setNewName(file.name)
                }}
                className="text-gray-400 hover:text-blue-500 transition-colors duration-200"
                title="Rename"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              
              {file.status === 'pending' && (
                <button
                  onClick={() => handleProcess(file.id)}
                  className="text-gray-400 hover:text-green-500 transition-colors duration-200"
                  title="Start Processing"
                >
                  <Play className="w-4 h-4" />
                </button>
              )}
              
              <button
                className="text-gray-400 hover:text-blue-500 transition-colors duration-200"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => handleDelete(file.id)}
                className="text-gray-400 hover:text-red-500 transition-colors duration-200"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 