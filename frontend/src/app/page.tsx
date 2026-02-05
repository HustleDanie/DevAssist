'use client';

import { useState } from 'react';
import { CodeSnippet } from '@/components/CodeSnippet';
import { RepoMigration } from '@/components/RepoMigration';
import { Header } from '@/components/Header';

type TabType = 'snippet' | 'repo';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('snippet');

  return (
    <main className="min-h-screen">
      <Header />
      
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Multi-Agent Code Migration
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Enterprise-grade automated code migration using LangGraph workflow.
            Supports Python 2→3 and Flask→FastAPI migrations.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-slate-100 dark:bg-slate-800 rounded-xl p-1 inline-flex">
            <button
              onClick={() => setActiveTab('snippet')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'snippet'
                  ? 'bg-white dark:bg-slate-700 text-primary-600 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                Code Snippet
              </span>
            </button>
            <button
              onClick={() => setActiveTab('repo')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'repo'
                  ? 'bg-white dark:bg-slate-700 text-primary-600 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                Full Repository
              </span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
          {activeTab === 'snippet' ? <CodeSnippet /> : <RepoMigration />}
        </div>

        {/* Features Section */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white text-center mb-8">
            Powered by Multi-Agent AI
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 text-center shadow-lg">
              <div className="w-14 h-14 bg-blue-100 dark:bg-blue-900 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📥</span>
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Git Clone
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Clone any repository automatically via GitHub API
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 text-center shadow-lg">
              <div className="w-14 h-14 bg-purple-100 dark:bg-purple-900 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔍</span>
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Planner Agent
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                AST parsing + LLM analysis to identify deprecated code
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 text-center shadow-lg">
              <div className="w-14 h-14 bg-green-100 dark:bg-green-900 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">💻</span>
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Coder Agent
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Rewrites code with MCP style guide context
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 text-center shadow-lg">
              <div className="w-14 h-14 bg-orange-100 dark:bg-orange-900 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🧪</span>
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Tester Agent
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Docker-based testing with automatic PR generation
              </p>
            </div>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mt-12 text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Built with <strong>Python</strong> • <strong>LangChain/LangGraph</strong> • <strong>FastAPI</strong> • <strong>Next.js</strong> • <strong>Docker</strong>
          </p>
        </div>
      </div>
    </main>
  );
}
