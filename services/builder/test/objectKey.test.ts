import { describe, it, expect } from 'vitest';
import { artifactKey } from '@metaagent/object-storage';

describe('Object Key Utils', () => {
  it('generates correct artifact key with default filename', () => {
    const key = artifactKey({
      userId: 'user-123',
      draftId: 'draft-456', 
      buildId: 'build-789'
    });
    
    expect(key).toBe('scaffolds/user-123/draft-456/build-789/project.zip');
  });

  it('generates correct artifact key with custom filename', () => {
    const key = artifactKey({
      userId: 'user-123',
      draftId: 'draft-456',
      buildId: 'build-789',
      filename: 'custom-project.zip'
    });
    
    expect(key).toBe('scaffolds/user-123/draft-456/build-789/custom-project.zip');
  });

  it('handles special characters in IDs', () => {
    const key = artifactKey({
      userId: 'user@domain.com',
      draftId: 'draft-with-dashes',
      buildId: 'build_with_underscores',
      filename: 'my project.zip'
    });
    
    expect(key).toBe('scaffolds/user@domain.com/draft-with-dashes/build_with_underscores/my project.zip');
  });

  it('ensures deterministic keys for same inputs', () => {
    const input = {
      userId: 'user-123',
      draftId: 'draft-456',
      buildId: 'build-789'
    };
    
    const key1 = artifactKey(input);
    const key2 = artifactKey(input);
    
    expect(key1).toBe(key2);
    expect(key1).toBe('scaffolds/user-123/draft-456/build-789/project.zip');
  });
});
