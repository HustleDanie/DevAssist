'use client';

import { useState, useEffect } from 'react';
import { migrateRepository, getJobStatus } from '@/lib/api';
import type { MigrationJob } from '@/types';

export function RepoMigration() {
  const [repoUrl, setRepoUrl] = useState('');
  const [migrationType, setMigrationType] = useState<'py2to3' | 'flask_to_fastapi'>('py2to3');
  const [autoCreatePR, setAutoCreatePR] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [job, setJob] = useState<MigrationJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll for job status updates
  useEffect(() => {
    if (!job || job.status === 'completed' || job.status === 'failed') {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const updatedJob = await getJobStatus(job.job_id);
        setJob(updatedJob);
        
        if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [job]);

  const handleMigrate = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setJob(null);

    try {
      const newJob = await migrateRepository(repoUrl, migrationType, autoCreatePR);
      setJob(newJob);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Migration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'planning': return 'bg-blue-100 text-blue-800';
      case 'coding': return 'bg-purple-100 text-purple-800';
      case 'testing': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAgentIcon = (agent: string | null) => {
    switch (agent) {
      case 'planner': return '🔍';
      case 'coder': return '💻';
      case 'tester': return '🧪';
      default: return '⏳';
    }
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="space-y-4">
        <div>
          <label htmlFor="repo-url" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            GitHub Repository URL
          </label>
          <input
            id="repo-url"
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="w-full px-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div className="flex flex-wrap gap-4">
          <div>
            <label htmlFor="migration-type" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Migration Type
            </label>
            <select
              id="migration-type"
              value={migrationType}
              onChange={(e) => setMigrationType(e.target.value as 'py2to3' | 'flask_to_fastapi')}
              className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500"
            >
              <option value="py2to3">Python 2 → Python 3</option>
              <option value="flask_to_fastapi">Flask → FastAPI</option>
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoCreatePR}
                onChange={(e) => setAutoCreatePR(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Auto-create Pull Request
              </span>
            </label>
          </div>
        </div>

        <button
          onClick={handleMigrate}
          disabled={isLoading || !repoUrl.trim()}
          className="w-full sm:w-auto px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Starting Migration...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Start Full Migration
            </>
          )}
        </button>

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}
      </div>

      {/* Job Progress Section */}
      {job && (
        <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-900 dark:text-white">
              Migration Progress
            </h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(job.status)}`}>
              {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
            </span>
          </div>

          {/* Progress Indicator */}
          <div className="flex items-center gap-2">
            {['cloning', 'planning', 'coding', 'testing', 'completed'].map((stage, index) => {
              const stages = ['cloning', 'planning', 'coding', 'testing', 'completed'];
              const currentIndex = stages.indexOf(job.status);
              const isActive = currentIndex >= index;
              const isCurrent = job.status === stage;
              
              return (
                <div key={stage} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    isActive 
                      ? 'bg-primary-600 text-white' 
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                  } ${isCurrent ? 'ring-2 ring-primary-400 ring-offset-2' : ''}`}>
                    {index + 1}
                  </div>
                  {index < stages.length - 1 && (
                    <div className={`w-8 h-1 ${isActive ? 'bg-primary-600' : 'bg-slate-200 dark:bg-slate-700'}`} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Current Agent */}
          {job.current_agent && job.status !== 'completed' && job.status !== 'failed' && (
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
              <span className="text-2xl">{getAgentIcon(job.current_agent)}</span>
              <span>
                <strong className="capitalize">{job.current_agent}</strong> agent is working...
              </span>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-slate-900 dark:text-white">{job.file_count}</div>
              <div className="text-xs text-slate-500">Files</div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-orange-600">{job.issues_found}</div>
              <div className="text-xs text-slate-500">Issues Found</div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600">{job.issues_fixed}</div>
              <div className="text-xs text-slate-500">Issues Fixed</div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold">
                {job.tests_passed === null ? '—' : job.tests_passed ? '✅' : '❌'}
              </div>
              <div className="text-xs text-slate-500">Tests</div>
            </div>
          </div>

          {/* PR Link */}
          {job.pr_url && (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-green-800 dark:text-green-200">
                  Pull request created!{' '}
                  <a href={job.pr_url} target="_blank" rel="noopener noreferrer" className="underline font-medium">
                    View PR →
                  </a>
                </span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {job.error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-600 dark:text-red-400">{job.error}</p>
            </div>
          )}

          {/* Message Log */}
          {job.messages && job.messages.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Activity Log</h4>
              <div className="bg-slate-900 rounded-lg p-4 max-h-48 overflow-y-auto">
                {job.messages.map((msg, index) => (
                  <div key={index} className="text-sm text-slate-300 font-mono">
                    <span className="text-slate-500">{`>`}</span> {msg}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Architecture Info */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-xl p-6">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
          Multi-Agent Workflow
        </h3>
        <div className="grid sm:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-3xl mb-2">📥</div>
            <div className="font-medium text-slate-900 dark:text-white">Git Clone</div>
            <div className="text-xs text-slate-500">Clone repository</div>
          </div>
          <div>
            <div className="text-3xl mb-2">🔍</div>
            <div className="font-medium text-slate-900 dark:text-white">Planner Agent</div>
            <div className="text-xs text-slate-500">AST analysis + LLM</div>
          </div>
          <div>
            <div className="text-3xl mb-2">💻</div>
            <div className="font-medium text-slate-900 dark:text-white">Coder Agent</div>
            <div className="text-xs text-slate-500">Rewrite with MCP context</div>
          </div>
          <div>
            <div className="text-3xl mb-2">🧪</div>
            <div className="font-medium text-slate-900 dark:text-white">Tester Agent</div>
            <div className="text-xs text-slate-500">Docker-based testing</div>
          </div>
        </div>
      </div>
    </div>
  );
}
