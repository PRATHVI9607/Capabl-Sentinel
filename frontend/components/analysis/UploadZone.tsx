'use client'

import { FilePdf, Trash, UploadSimple } from '@phosphor-icons/react'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

import { getSampleReport } from '@/lib/api'
import { MAX_UPLOAD_BYTES } from '@/lib/constants'
import { cn, formatFileSize } from '@/lib/utils'

interface UploadZoneProps { onAnalyze: (file: File) => void; loading?: boolean; initialError?: string | null }

function validateFile(file: File) {
  if (!file.name.toLowerCase().endsWith('.pdf') || file.type !== 'application/pdf') return 'Choose a PDF file. Other document formats are not accepted.'
  if (file.size < 100) return 'This PDF is empty or too small to contain a report.'
  if (file.size > MAX_UPLOAD_BYTES) return 'This PDF is larger than the 10MB upload limit.'
  return null
}

export function UploadZone({ onAnalyze, loading = false, initialError }: UploadZoneProps) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(initialError ?? null)
  const [sampleLoading, setSampleLoading] = useState(false)
  const acceptFile = useCallback((nextFile: File) => { const issue = validateFile(nextFile); setError(issue); setFile(issue ? null : nextFile) }, [])
  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop: (acceptedFiles) => acceptedFiles[0] ? acceptFile(acceptedFiles[0]) : setError('Choose one PDF file up to 10MB.'),
    multiple: false, noClick: true, maxSize: MAX_UPLOAD_BYTES, accept: { 'application/pdf': ['.pdf'] }, disabled: loading,
  })
  const selectSample = async () => {
    setSampleLoading(true); setError(null)
    try { acceptFile(await getSampleReport()) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'The sample report is unavailable.') }
    finally { setSampleLoading(false) }
  }
  return (
    <div {...getRootProps()} className={cn('space-y-3', isDragActive && 'upload-active')}>
      <input {...getInputProps()} aria-label="Upload incident report PDF" />
      {file ? (
        <div className="border border-border-default bg-bg-surface p-4">
          <div className="flex items-center gap-3">
            <FilePdf size={25} weight="light" className="shrink-0 text-accent" />
            <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{file.name}</p><p className="mt-1 font-mono text-[10px] text-text-muted">{formatFileSize(file.size)}</p></div>
            <button type="button" aria-label="Remove file" className="grid h-9 w-9 place-items-center text-text-muted hover:text-text-primary" onClick={() => { setFile(null); setError(null) }}><Trash size={18} weight="light" /></button>
          </div>
          <button type="button" disabled={loading} className="control-primary mt-4 flex h-14 w-full items-center justify-center gap-3 px-5 text-sm font-semibold" onClick={() => onAnalyze(file)}><UploadSimple size={20} weight="light" />{loading ? 'Starting analysis' : 'Run analysis'}</button>
        </div>
      ) : (
        <>
          <button type="button" className="control-primary flex h-14 w-full items-center justify-center gap-3 px-5 text-sm font-semibold" onClick={open}><FilePdf size={21} weight="light" /> Select incident report</button>
          <button type="button" disabled={sampleLoading} className="control-secondary flex h-14 w-full items-center justify-center gap-3 px-5 text-sm font-medium" onClick={() => void selectSample()}><UploadSimple size={19} weight="light" />{sampleLoading ? 'Loading sample' : 'Try a sample OSHA report'}</button>
          <p className="pt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-text-muted">PDF, up to 10 MB · drag and drop supported</p>
        </>
      )}
      {error ? <p role="alert" className="border-l-2 border-severity-critical bg-severity-critical/[0.06] px-4 py-3 text-sm text-severity-critical">{error}</p> : null}
    </div>
  )
}
