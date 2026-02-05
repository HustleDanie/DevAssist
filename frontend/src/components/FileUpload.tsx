'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileArchive, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { MigrationJob } from '@/types';
import { cn, formatFileSize } from '@/lib/utils';

interface FileUploadProps {
  onUploadStart: (job: MigrationJob) => void;
}

type MigrationType = 'py2to3' | 'flask_to_fastapi';

export function FileUpload({ onUploadStart }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [migrationType, setMigrationType] = useState<MigrationType>('py2to3');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        setError('Please upload a ZIP file');
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const job = await api.startMigration(selectedFile, migrationType);
      onUploadStart(job);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start migration');
      setIsUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Migration Type Selection */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          Migration Type
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => setMigrationType('py2to3')}
            className={cn(
              'p-4 rounded-xl border-2 transition-all text-left',
              migrationType === 'py2to3'
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30'
                : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
            )}
          >
            <div className="font-semibold text-slate-900 dark:text-white mb-1">
              Python 2 → 3
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">
              Migrate legacy Python 2 code to Python 3
            </div>
          </button>

          <button
            type="button"
            onClick={() => setMigrationType('flask_to_fastapi')}
            className={cn(
              'p-4 rounded-xl border-2 transition-all text-left',
              migrationType === 'flask_to_fastapi'
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30'
                : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
            )}
          >
            <div className="font-semibold text-slate-900 dark:text-white mb-1">
              Flask → FastAPI
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">
              Upgrade Flask apps to modern FastAPI
            </div>
          </button>
        </div>
      </div>

      {/* Dropzone */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          Upload Codebase
        </label>

        {!selectedFile ? (
          <div
            {...getRootProps()}
            className={cn(
              'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
              isDragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30'
                : 'border-slate-300 dark:border-slate-600 hover:border-primary-400 dark:hover:border-primary-500'
            )}
          >
            <input {...getInputProps()} />
            <Upload
              className={cn(
                'w-12 h-12 mx-auto mb-4',
                isDragActive
                  ? 'text-primary-500'
                  : 'text-slate-400 dark:text-slate-500'
              )}
            />
            <p className="text-slate-600 dark:text-slate-300 mb-2">
              {isDragActive
                ? 'Drop the ZIP file here...'
                : 'Drag & drop your ZIP file here, or click to browse'}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Upload a ZIP file from your GitHub repository
            </p>
          </div>
        ) : (
          <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                  <FileArchive className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
              >
                Remove
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 p-4 rounded-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isUploading}
        className={cn(
          'w-full py-4 rounded-xl font-semibold text-white transition-all',
          selectedFile && !isUploading
            ? 'bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 shadow-lg shadow-primary-500/25'
            : 'bg-slate-300 dark:bg-slate-700 cursor-not-allowed'
        )}
      >
        {isUploading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Uploading...
          </span>
        ) : (
          'Start Migration'
        )}
      </button>
    </div>
  );
}
