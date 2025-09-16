import pg from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import { sql } from 'drizzle-orm';
import { pgTable, uuid, text, jsonb, timestamp, boolean, index, bigint, serial, integer } from 'drizzle-orm/pg-core';

const { Pool } = pg;

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export const db = drizzle(pool);

// Schema definitions
export const appUsers = pgTable('app_users', {
  id: uuid('id').primaryKey(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow(),
});

export const specDrafts = pgTable('spec_drafts', {
  id: uuid('id').primaryKey().defaultRandom(),
  ownerUserId: uuid('owner_user_id').notNull().references(() => appUsers.id, { onDelete: 'cascade' }),
  templateId: text('template_id'),
  name: text('name').notNull(), // kept for backwards compatibility
  title: text('title').notNull(),
  spec: jsonb('spec').notNull(),
  isDraft: boolean('is_draft').default(true),
  status: text('status').default('DRAFT'), // DRAFT or PUBLISHED
  tags: text('tags').array().default([]),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
}, (table) => ({
  ownerIdx: index('idx_spec_drafts_owner').on(table.ownerUserId, table.updatedAt.desc()),
  templateIdx: index('idx_spec_drafts_template').on(table.templateId),
  statusIdx: index('idx_spec_drafts_status').on(table.status, table.updatedAt.desc()),
}));

export const builderArtifacts = pgTable('builder_artifacts', {
  id: uuid('id').primaryKey().defaultRandom(),
  draftId: uuid('draft_id').notNull().references(() => specDrafts.id, { onDelete: 'cascade' }),
  buildId: text('build_id').notNull(),
  step: text('step').notNull().default('scaffold'),
  bucket: text('bucket').notNull(),
  objectKey: text('object_key').notNull(),
  sizeBytes: bigint('size_bytes', { mode: 'number' }),
  etag: text('etag'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const gateResults = pgTable('gate_results', {
  id: serial('id').primaryKey(),
  draftId: uuid('draft_id').notNull().references(() => specDrafts.id, { onDelete: 'cascade' }),
  buildId: text('build_id').notNull(),
  gateName: text('gate_name').notNull(),
  passed: boolean('passed').notNull(),
  durationMs: integer('duration_ms').notNull(),
  errors: jsonb('errors'),
  warnings: jsonb('warnings'),
  metadata: jsonb('metadata'),
  createdAt: timestamp('created_at').defaultNow(),
}, (table) => ({
  draftIdx: index('idx_gate_results_draft_id').on(table.draftId),
  buildIdx: index('idx_gate_results_build_id').on(table.buildId),
}));

export const gateRuns = pgTable('gate_runs', {
  id: serial('id').primaryKey(),
  draftId: uuid('draft_id').notNull().references(() => specDrafts.id, { onDelete: 'cascade' }),
  buildId: text('build_id').notNull(),
  success: boolean('success').notNull(),
  totalDurationMs: integer('total_duration_ms').notNull(),
  failedGate: text('failed_gate'),
  createdAt: timestamp('created_at').defaultNow(),
}, (table) => ({
  draftIdx: index('idx_gate_runs_draft_id').on(table.draftId),
  buildIdx: index('idx_gate_runs_build_id').on(table.buildId),
}));

// Helper function to set app user context for RLS
export async function setAppUser(userId: string) {
  await db.execute(sql`SELECT set_app_user(${userId}::uuid)`);
}

// Types
export type SpecDraft = typeof specDrafts.$inferSelect;
export type NewSpecDraft = typeof specDrafts.$inferInsert;
export type BuilderArtifact = typeof builderArtifacts.$inferSelect;
export type GateResult = typeof gateResults.$inferSelect;
export type NewGateResult = typeof gateResults.$inferInsert;
export type GateRun = typeof gateRuns.$inferSelect;
export type NewGateRun = typeof gateRuns.$inferInsert;

