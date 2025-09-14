import { describe, it, expect, vi } from 'vitest';

vi.mock('@metaagent/db', () => {
  const rows: any[] = [];
  const specDrafts = {} as any;

  const db = {
    update: () => ({
      set: (_values: any) => ({
        where: (_expr: any) => ({
          returning: () => ([] as any[])
        })
      })
    }),
    insert: () => ({
      values: (v: any) => ({
        returning: () => {
          const id = `db-${rows.length + 1}`;
          const rec = { id, ...v };
          rows.push(rec);
          return [rec];
        }
      })
    }),
  } as any;

  const setAppUser = async (_id: string) => {};

  return { db, specDrafts, setAppUser };
});

import { handleDraftAutosave } from '../src/handlers/draftAutosave';

describe('handleDraftAutosave', () => {
  it('inserts new draft when no id provided', async () => {
    const res = await handleDraftAutosave({ userId: 'u1', draft: { title: 'T', payload: { a: 1 } } } as any);
    expect(res.id).toBeDefined();
    expect(typeof res.updatedAt).toBe('string');
  });
});
