import { describe, it, expect } from 'vitest';
import { createDraftSpec, updateDraftSpec, isDraftSpec } from './draft';
import { ulid } from 'ulid';

describe('Draft Helpers', () => {
  it('should create a draft spec with defaults', () => {
    const draft = createDraftSpec();
    
    expect(draft.title).toBe('Untitled Agent');
    expect(draft.isDraft).toBe(true);
    expect(draft.status).toBe('DRAFT');
    expect(draft.id).toBeDefined();
    expect(draft.createdAt).toBeDefined();
    expect(draft.updatedAt).toBeDefined();
    expect(draft.payload).toEqual({});
  });

  it('should create a draft spec with custom input', () => {
    const input = {
      title: 'Custom Agent',
      payload: { meta: { name: 'test-agent' } },
      templateId: 'chatbot'
    };

    const draft = createDraftSpec(input);
    
    expect(draft.title).toBe('Custom Agent');
    expect(draft.payload).toEqual({ meta: { name: 'test-agent' } });
  });

  it('should update an existing draft spec', () => {
    const original = createDraftSpec({ title: 'Original' });
    const updated = updateDraftSpec(original, { 
      title: 'Updated',
      payload: { 
        meta: { 
          id: ulid(),
          name: 'test-name',
          version: '1.0.0',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          description: 'Updated description' 
        } 
      }
    });
    
    expect(updated.title).toBe('Updated');
    expect(updated.payload?.meta?.description).toBe('Updated description');
    expect(updated.id).toBe(original.id);
    expect(new Date(updated.updatedAt).getTime()).toBeGreaterThanOrEqual(new Date(original.updatedAt).getTime());
  });

  it('should validate draft specs correctly', () => {
    const validDraft = createDraftSpec();
    expect(isDraftSpec(validDraft)).toBe(true);
    
    const invalidDraft = { title: 'Invalid' }; // missing required fields
    expect(isDraftSpec(invalidDraft)).toBe(false);
    
    expect(isDraftSpec(null)).toBe(false);
    expect(isDraftSpec(undefined)).toBe(false);
    expect(isDraftSpec('not an object')).toBe(false);
  });
});
