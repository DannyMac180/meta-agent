import pg from 'pg';
import { drizzle } from 'drizzle-orm/node-postgres';
import { sql } from 'drizzle-orm';
import { pgTable, uuid, text, jsonb, timestamp, boolean, index } from 'drizzle-orm/pg-core';

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

// Helper function to set app user context for RLS
export async function setAppUser(userId: string) {
  await db.execute(sql`SELECT set_app_user(${userId}::uuid)`);
}

// Types
export type SpecDraft = typeof specDrafts.$inferSelect;
export type NewSpecDraft = typeof specDrafts.$inferInsert;
