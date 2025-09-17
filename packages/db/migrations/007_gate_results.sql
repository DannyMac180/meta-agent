-- Gate results table to store quality gate execution results
CREATE TABLE gate_results (
    id SERIAL PRIMARY KEY,
    draft_id UUID REFERENCES spec_drafts(id) ON DELETE CASCADE,
    build_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    duration_ms INTEGER NOT NULL,
    errors JSONB,
    warnings JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Gate runs table to store overall gate run results
CREATE TABLE gate_runs (
    id SERIAL PRIMARY KEY,
    draft_id UUID REFERENCES spec_drafts(id) ON DELETE CASCADE,
    build_id TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    failed_gate TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for common queries
CREATE INDEX idx_gate_results_draft_id ON gate_results(draft_id);
CREATE INDEX idx_gate_results_build_id ON gate_results(build_id);
CREATE INDEX idx_gate_runs_draft_id ON gate_runs(draft_id);
CREATE INDEX idx_gate_runs_build_id ON gate_runs(build_id);

-- Row Level Security
ALTER TABLE gate_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE gate_runs ENABLE ROW LEVEL SECURITY;

-- RLS policies (users can only see their own gate results)
CREATE POLICY gate_results_user_policy ON gate_results
  FOR ALL TO app_user
  USING (
    EXISTS (
      SELECT 1 FROM spec_drafts 
      WHERE spec_drafts.id = gate_results.draft_id 
      AND spec_drafts.owner_user_id = current_setting('app.user_id')::uuid
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM spec_drafts 
      WHERE spec_drafts.id = gate_results.draft_id 
      AND spec_drafts.owner_user_id = current_setting('app.user_id')::uuid
    )
  );

CREATE POLICY gate_runs_user_policy ON gate_runs
  FOR ALL TO app_user
  USING (
    EXISTS (
      SELECT 1 FROM spec_drafts 
      WHERE spec_drafts.id = gate_runs.draft_id 
      AND spec_drafts.owner_user_id = current_setting('app.user_id')::uuid
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM spec_drafts 
      WHERE spec_drafts.id = gate_runs.draft_id 
      AND spec_drafts.owner_user_id = current_setting('app.user_id')::uuid
    )
  );
