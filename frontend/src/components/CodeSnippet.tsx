'use client';

import { useState } from 'react';
import { Play, Copy, Check, AlertCircle, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { SnippetResponse } from '@/types';
import { cn } from '@/lib/utils';

type MigrationType = 'py2to3' | 'flask_to_fastapi';

const EXAMPLE_PY2_CODE = `# Python 2 Example Code
print "Hello, World!"

# Using raw_input (Python 2)
name = raw_input("Enter your name: ")
print "Hello, " + name

# Using xrange (Python 2)
for i in xrange(10):
    print i

# Dictionary iteration (Python 2)
my_dict = {"a": 1, "b": 2}
for key, value in my_dict.iteritems():
    print key, value

# Using unicode literals
text = u"Hello Unicode"
`;

const EXAMPLE_FLASK_CODE = `# Flask Example Code
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
    return jsonify(users)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({"id": user_id, "name": "John"})

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify(data), 201

if __name__ == '__main__':
    app.run(debug=True)
`;

export function CodeSnippet() {
  const [code, setCode] = useState('');
  const [migrationType, setMigrationType] = useState<MigrationType>('py2to3');
  const [result, setResult] = useState<SnippetResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleMigrate = async () => {
    if (!code.trim()) {
      setError('Please enter some code to migrate');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.migrateSnippet(code, migrationType);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Migration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (result?.migrated_code) {
      await navigator.clipboard.writeText(result.migrated_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const loadExample = () => {
    setCode(migrationType === 'py2to3' ? EXAMPLE_PY2_CODE : EXAMPLE_FLASK_CODE);
    setResult(null);
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
            onClick={() => {
              setMigrationType('py2to3');
              setResult(null);
            }}
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
            onClick={() => {
              setMigrationType('flask_to_fastapi');
              setResult(null);
            }}
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

      {/* Code Input */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Input Code
          </label>
          <button
            onClick={loadExample}
            className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center gap-1"
          >
            <Sparkles className="w-4 h-4" />
            Load Example
          </button>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder={`Paste your ${migrationType === 'py2to3' ? 'Python 2' : 'Flask'} code here...`}
          className="w-full h-64 p-4 rounded-xl border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 p-4 rounded-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Migrate Button */}
      <button
        onClick={handleMigrate}
        disabled={!code.trim() || isLoading}
        className={cn(
          'w-full py-4 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2',
          code.trim() && !isLoading
            ? 'bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 shadow-lg shadow-primary-500/25'
            : 'bg-slate-300 dark:bg-slate-700 cursor-not-allowed'
        )}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Migrating...
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            Migrate Code
          </>
        )}
      </button>

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {/* Stats */}
          <div className="flex items-center justify-center gap-6 py-4 bg-green-50 dark:bg-green-950/30 rounded-xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {result.issues_found}
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-400">
                Issues Found
              </div>
            </div>
            <div className="w-px h-10 bg-green-200 dark:bg-green-800" />
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {result.issues_fixed}
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-400">
                Issues Fixed
              </div>
            </div>
          </div>

          {/* Migrated Code */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Migrated Code
              </label>
              <button
                onClick={handleCopy}
                className="text-sm text-slate-600 dark:text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-green-500" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy
                  </>
                )}
              </button>
            </div>
            <pre className="w-full h-64 p-4 rounded-xl border border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-950/30 text-slate-900 dark:text-white font-mono text-sm overflow-auto">
              {result.migrated_code}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
