'use client'

import { useState, useCallback } from 'react'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import Link from 'next/link'

const REPORT_TYPES = [
  { id: 'organic_keywords', name: 'Organic Keywords', icon: '🔑' },
  { id: 'serp_overview', name: 'SERP Overview', icon: '🔍' },
  { id: 'backlinks', name: 'Backlinks', icon: '🔗' },
  { id: 'referring_domains', name: 'Referring Domains', icon: '🌐' },
  { id: 'matching_terms_keywords', name: 'Matching Terms (Keywords)', icon: '📊' },
  { id: 'matching_terms_clusters', name: 'Matching Terms (Clusters)', icon: '📈' },
  { id: 'clusters', name: 'Clusters by Parent Topic', icon: '🎯' },
  { id: 'organic_competitors', name: 'Organic Competitors', icon: '⚔️' },
  { id: 'best_by_links', name: 'Best by Links', icon: '🏆' },
  { id: 'internal_links', name: 'Internal Most Linked', icon: '🔗' },
]

interface UploadedFile {
  file: File
  reportType: string
  isPrimary: boolean
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  uploadId?: string
  error?: string
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.name.endsWith('.csv')
    )

    if (droppedFiles.length > 0) {
      addFiles(droppedFiles)
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(Array.from(e.target.files))
    }
  }

  const addFiles = (newFiles: File[]) => {
    const uploadedFiles: UploadedFile[] = newFiles.map((file, index) => ({
      file,
      reportType: index === 0 ? 'organic_keywords' : '',
      isPrimary: index === 0,
      status: 'pending',
      progress: 0,
    }))
    setFiles(prev => [...prev, ...uploadedFiles])
  }

  const updateFile = (index: number, updates: Partial<UploadedFile>) => {
    setFiles(prev => prev.map((f, i) => i === index ? { ...f, ...updates } : f))
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const uploadFile = async (index: number) => {
    const fileData = files[index]
    if (!fileData.reportType) {
      updateFile(index, { status: 'error', error: 'Please select report type' })
      return
    }

    updateFile(index, { status: 'uploading', progress: 0 })

    const formData = new FormData()
    formData.append('file', fileData.file)
    formData.append('user_id', 'demo-user') // TODO: Real user ID
    formData.append('is_primary', String(fileData.isPrimary))

    try {
      const response = await fetch('http://localhost:8000/api/v1/upload/ahrefs', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()

      updateFile(index, {
        status: 'success',
        progress: 100,
        uploadId: data.upload_id,
      })
    } catch (error) {
      updateFile(index, {
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed',
      })
    }
  }

  const uploadAll = async () => {
    const pendingFiles = files
      .map((f, i) => ({ file: f, index: i }))
      .filter(({ file }) => file.status === 'pending' && file.reportType)

    for (const { index } of pendingFiles) {
      await uploadFile(index)
    }
  }

  const successCount = files.filter(f => f.status === 'success').length
  const errorCount = files.filter(f => f.status === 'error').length
  const pendingCount = files.filter(f => f.status === 'pending').length

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-4 border-primary p-6 shadow-brutal-lg">
        <h1 className="text-brutal-xl text-primary mb-4">UPLOAD AHREFS DATA</h1>
        <p className="text-lg">
          Upload your Ahrefs CSV exports. We'll extract <span className="text-primary font-bold">EVERY strategic insight</span> they hide.
        </p>
      </div>

      {/* Instructions */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="border-4 border-secondary p-6">
          <div className="text-brutal-md mb-4">1️⃣ EXPORT</div>
          <p className="text-sm">
            Download your data from Ahrefs as CSV files. All 10 report types supported.
          </p>
        </div>

        <div className="border-4 border-secondary p-6">
          <div className="text-brutal-md mb-4">2️⃣ UPLOAD</div>
          <p className="text-sm">
            Drag & drop or click to upload. Mark YOUR site as primary, competitors as secondary.
          </p>
        </div>

        <div className="border-4 border-secondary p-6">
          <div className="text-brutal-md mb-4">3️⃣ ANALYZE</div>
          <p className="text-sm">
            Run any of 20+ intelligence modes. Get AI-powered insights in seconds.
          </p>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          border-4 border-dashed p-12 text-center transition-all
          ${dragActive ? 'border-primary bg-primary/10 shadow-brutal-lg' : 'border-secondary'}
        `}
      >
        <Upload className="w-16 h-16 mx-auto mb-4 text-primary" />
        <p className="text-xl font-bold mb-2">Drop Ahrefs CSV files here</p>
        <p className="text-muted mb-4">or</p>
        <label className="inline-block px-6 py-3 bg-primary text-white font-bold shadow-brutal hover:shadow-brutal-lg transition-shadow cursor-pointer">
          SELECT FILES
          <input
            type="file"
            multiple
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
          />
        </label>
        <p className="text-sm text-muted mt-4">Supports all 10 Ahrefs report types</p>
      </div>

      {/* Uploaded Files */}
      {files.length > 0 && (
        <div className="border-4 border-secondary p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-brutal-md">UPLOADED FILES ({files.length})</h2>
            <div className="flex gap-4 text-sm">
              <span className="text-accent">✓ {successCount} success</span>
              {errorCount > 0 && <span className="text-primary">✗ {errorCount} errors</span>}
              {pendingCount > 0 && <span className="text-muted">○ {pendingCount} pending</span>}
            </div>
          </div>

          <div className="space-y-4">
            {files.map((fileData, index) => (
              <FileRow
                key={index}
                fileData={fileData}
                index={index}
                onUpdate={(updates) => updateFile(index, updates)}
                onRemove={() => removeFile(index)}
                onUpload={() => uploadFile(index)}
              />
            ))}
          </div>

          {pendingCount > 0 && (
            <button
              onClick={uploadAll}
              className="mt-6 w-full py-4 bg-primary text-white font-bold shadow-brutal hover:shadow-brutal-lg transition-shadow"
            >
              UPLOAD ALL ({pendingCount} FILES)
            </button>
          )}

          {successCount > 0 && (
            <Link
              href="/modes"
              className="mt-4 block text-center py-4 border-4 border-accent text-accent font-bold shadow-brutal hover:shadow-brutal-lg transition-shadow"
            >
              PROCEED TO INTELLIGENCE MODES →
            </Link>
          )}
        </div>
      )}

      {/* Supported Report Types */}
      <div className="border-4 border-secondary p-6">
        <h2 className="text-brutal-md mb-6">SUPPORTED REPORT TYPES</h2>
        <div className="grid md:grid-cols-5 gap-4">
          {REPORT_TYPES.map(type => (
            <div key={type.id} className="border-2 border-secondary/30 p-3 text-center">
              <div className="text-2xl mb-2">{type.icon}</div>
              <div className="text-xs font-mono">{type.name}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FileRow({
  fileData,
  index,
  onUpdate,
  onRemove,
  onUpload,
}: {
  fileData: UploadedFile
  index: number
  onUpdate: (updates: Partial<UploadedFile>) => void
  onRemove: () => void
  onUpload: () => void
}) {
  const statusIcons = {
    pending: <AlertCircle className="w-5 h-5 text-muted" />,
    uploading: <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />,
    success: <CheckCircle className="w-5 h-5 text-accent" />,
    error: <AlertCircle className="w-5 h-5 text-primary" />,
  }

  return (
    <div className="border-2 border-secondary/50 p-4 flex items-center gap-4">
      {statusIcons[fileData.status]}

      <FileText className="w-5 h-5" />

      <div className="flex-1 min-w-0">
        <div className="font-mono text-sm truncate">{fileData.file.name}</div>
        <div className="text-xs text-muted">
          {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
        </div>
      </div>

      <select
        value={fileData.reportType}
        onChange={(e) => onUpdate({ reportType: e.target.value })}
        className="px-3 py-2 border-2 border-secondary font-mono text-sm"
        disabled={fileData.status !== 'pending'}
      >
        <option value="">Select type...</option>
        {REPORT_TYPES.map(type => (
          <option key={type.id} value={type.id}>{type.name}</option>
        ))}
      </select>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={fileData.isPrimary}
          onChange={(e) => onUpdate({ isPrimary: e.target.checked })}
          disabled={fileData.status !== 'pending'}
          className="w-4 h-4"
        />
        <span className="text-sm">Primary</span>
      </label>

      {fileData.status === 'pending' && (
        <button
          onClick={onUpload}
          disabled={!fileData.reportType}
          className="px-4 py-2 bg-primary text-white text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          UPLOAD
        </button>
      )}

      {fileData.status === 'error' && (
        <div className="text-xs text-primary">{fileData.error}</div>
      )}

      <button
        onClick={onRemove}
        className="p-2 hover:bg-secondary/10"
        disabled={fileData.status === 'uploading'}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
