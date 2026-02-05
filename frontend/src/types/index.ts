export interface MigrationJob {
  job_id: string;
  status: 'pending' | 'processing' | 'cloning' | 'planning' | 'coding' | 'testing' | 'review' | 'completed' | 'failed';
  migration_type: 'py2to3' | 'flask_to_fastapi';
  created_at: string;
  completed_at?: string;
  error?: string;
  file_count: number;
  issues_found: number;
  issues_fixed: number;
  tests_passed?: boolean;
  pr_url?: string;
  current_agent?: 'planner' | 'coder' | 'tester';
  messages?: string[];
}

export interface SnippetResponse {
  original_code: string;
  migrated_code: string;
  issues_found: number;
  issues_fixed: number;
  migration_type: string;
}

export interface ApiError {
  detail: string;
}
