'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Menu, X, Upload, FileText, Activity, Settings } from 'lucide-react'

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen)

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">PoseDetect</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="flex items-center space-x-1 text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              <Upload className="w-4 h-4" />
              <span>Upload</span>
            </Link>
            <Link
              href="/files"
              className="flex items-center space-x-1 text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              <FileText className="w-4 h-4" />
              <span>Files</span>
            </Link>
            <Link
              href="/processing"
              className="flex items-center space-x-1 text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              <Activity className="w-4 h-4" />
              <span>Processing</span>
            </Link>
            <Link
              href="/settings"
              className="flex items-center space-x-1 text-gray-600 hover:text-primary-600 transition-colors duration-200"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={toggleMenu}
              className="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-md p-2"
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-2 space-y-1">
            <Link
              href="/"
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-md transition-colors duration-200"
              onClick={() => setIsMenuOpen(false)}
            >
              <Upload className="w-4 h-4" />
              <span>Upload</span>
            </Link>
            <Link
              href="/files"
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-md transition-colors duration-200"
              onClick={() => setIsMenuOpen(false)}
            >
              <FileText className="w-4 h-4" />
              <span>Files</span>
            </Link>
            <Link
              href="/processing"
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-md transition-colors duration-200"
              onClick={() => setIsMenuOpen(false)}
            >
              <Activity className="w-4 h-4" />
              <span>Processing</span>
            </Link>
            <Link
              href="/settings"
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-md transition-colors duration-200"
              onClick={() => setIsMenuOpen(false)}
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
} 