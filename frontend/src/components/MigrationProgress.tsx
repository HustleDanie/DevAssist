'use client';

import { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, XCircle, FileCode2, Bug, Wrench } from 'lucide-react';
import { api } from '@/lib/api';
import { MigrationJob } from '@/types';
import { cn, formatDuration } from '@/lib/utils';

interface MigrationProgressProps {
  job: MigrationJob;
  onComplete: (job: MigrationJob) => void;
  onError: () => void;
}

export function MigrationProgress({ job, onComplete, onError }: MigrationProgressProps) {
  const [currentJob, setCurrentJob] = useState<MigrationJob>(job);
  const [pollCount, setPollCount] = useState(0);

  useEffect(() => {
    if (currentJob.status === 'completed' || currentJob.status === 'failed') {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const updatedJob = await api.getJobStatus(currentJob.job_id);
        setCurrentJob(updatedJob);
        setPollCount((prev) => prev + 1);

        if (updatedJob.status === 'completed') {
          clearInterval(pollInterval);
          onComplete(updatedJob);
        } else if (updatedJob.status === 'failed') {
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [currentJob.job_id, currentJob.status, onComplete]);

  const getStatusIcon = () => {
    switch (currentJob.status) {
      case 'pending':
      case 'processing':
        return <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-8 h-8 text-green-500" />;
      case 'failed':
        return <XCircle className="w-8 h-8 text-red-500" />;
    }
  };

  const getStatusText = () => {
    switch (currentJob.status) {
      case 'pending':
        return 'Preparing migration...';
      case 'processing':
        return 'Processing your codebase...';
      case 'completed':
        return 'Migration completed!';
      case 'failed':
        return 'Migration failed';
    }
  };

  const getProgressSteps = () => {
    const steps = [
      { name: 'Upload', completed: true },
      { name: 'Analyze', completed: currentJob.status !== 'pending' },
      { name: 'Migrate', completed: currentJob.status === 'completed' || (currentJob.status === 'processing' && currentJob.issues_fixed > 0) },
      { name: 'Complete', completed: currentJob.status === 'completed' },
    ];
    return steps;
  };

  return (
    <div className="space-y-8">
      {/* Status Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-700 mb-4">
          {getStatusIcon()}
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {getStatusText()}
        </h2>
        <p className="text-slate-600 dark:text-slate-400">
          {currentJob.migration_type === 'py2to3'
            ? 'Python 2 → Python 3'
            : 'Flask → FastAPI'}
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex justify-between items-center">
        {getProgressSteps().map((step, index) => (
          <div key={step.name} className="flex items-center">
            <div
              className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm',
                step.completed
                  ? 'bg-primary-500 text-white'
                  : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
              )}
            >
              {step.completed ? '✓' : index + 1}
            </div>
            {index < 3 && (
              <div
                className={cn(
                  'w-16 sm:w-24 h-1 mx-2',
                  step.completed
                    ? 'bg-primary-500'
                    : 'bg-slate-200 dark:bg-slate-700'
                )}
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 px-2">
        {getProgressSteps().map((step) => (
          <span key={step.name}>{step.name}</span>
        ))}
      </div>

      {/* Stats */}
      {(currentJob.status === 'processing' || currentJob.status === 'completed') && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 text-center">
            <FileCode2 className="w-6 h-6 text-slate-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentJob.file_count}
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Files Processed
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 text-center">
            <Bug className="w-6 h-6 text-amber-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentJob.issues_found}
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Issues Found
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 text-center">
            <Wrench className="w-6 h-6 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentJob.issues_fixed}
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Issues Fixed
            </div>
          </div>
        </div>
      )}

      {/* Processing Animation */}
      {currentJob.status === 'processing' && (
        <div className="relative">
          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary-500 via-primary-400 to-primary-500 animate-gradient rounded-full w-full" />
          </div>
          <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-3">
            Elapsed time: {formatDuration(currentJob.created_at)}
          </p>
        </div>
      )}

      {/* Error Message */}
      {currentJob.status === 'failed' && currentJob.error && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">
            {currentJob.error}
          </p>
          <button
            onClick={onError}
            className="mt-3 text-sm font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
