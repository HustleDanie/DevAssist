'use client';

import { useState } from 'react';
import { Download, CheckCircle2, FileCode2, Bug, Wrench, RotateCcw } from 'lucide-react';
import { api } from '@/lib/api';
import { MigrationJob } from '@/types';
import { formatDuration } from '@/lib/utils';

interface DownloadResultProps {
  job: MigrationJob;
  onReset: () => void;
}

export function DownloadResult({ job, onReset }: DownloadResultProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const blob = await api.downloadResult(job.job_id);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `migrated-${job.job_id.slice(0, 8)}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  const duration = job.completed_at
    ? formatDuration(job.created_at, job.completed_at)
    : 'N/A';

  return (
    <div className="space-y-8">
      {/* Success Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
          <CheckCircle2 className="w-10 h-10 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Migration Complete!
        </h2>
        <p className="text-slate-600 dark:text-slate-400">
          Your codebase has been successfully migrated
        </p>
      </div>

      {/* Summary Stats */}
      <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-6">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
          Migration Summary
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <FileCode2 className="w-6 h-6 text-primary-500 mx-auto mb-2" />
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {job.file_count}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Files Processed
            </div>
          </div>

          <div className="text-center">
            <Bug className="w-6 h-6 text-amber-500 mx-auto mb-2" />
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {job.issues_found}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Issues Found
            </div>
          </div>

          <div className="text-center">
            <Wrench className="w-6 h-6 text-green-500 mx-auto mb-2" />
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {job.issues_fixed}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Issues Fixed
            </div>
          </div>

          <div className="text-center">
            <svg
              className="w-6 h-6 text-blue-500 mx-auto mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {duration}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Duration
            </div>
          </div>
        </div>
      </div>

      {/* Migration Type Badge */}
      <div className="flex justify-center">
        <span className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium">
          {job.migration_type === 'py2to3' ? (
            <>
              <span>🐍</span> Python 2 → Python 3
            </>
          ) : (
            <>
              <span>⚡</span> Flask → FastAPI
            </>
          )}
        </span>
      </div>

      {/* Download Button */}
      <button
        onClick={handleDownload}
        disabled={isDownloading}
        className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-lg shadow-green-500/25 transition-all flex items-center justify-center gap-2"
      >
        {isDownloading ? (
          <>
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
            Preparing Download...
          </>
        ) : (
          <>
            <Download className="w-5 h-5" />
            Download Migrated Code
          </>
        )}
      </button>

      {/* Start New Migration */}
      <button
        onClick={onReset}
        className="w-full py-3 rounded-xl font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-all flex items-center justify-center gap-2"
      >
        <RotateCcw className="w-4 h-4" />
        Start New Migration
      </button>
    </div>
  );
}
