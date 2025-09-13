import { describe, it, expect } from 'vitest';
import { templates, chatbotTemplate, webAutomationTemplate, apiCopilotTemplate } from './templates';
import { isDraftSpec } from '@metaagent/spec';

describe('Templates', () => {
  it('should export an array of templates', () => {
    expect(Array.isArray(templates)).toBe(true);
    expect(templates.length).toBeGreaterThan(0);
  });

  it('should have valid template structure', () => {
    templates.forEach(template => {
      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('description');
      expect(template).toHaveProperty('category');
      expect(template).toHaveProperty('defaultSpec');
      expect(typeof template.id).toBe('string');
      expect(typeof template.name).toBe('string');
      expect(typeof template.description).toBe('string');
    });
  });

  it('should have valid default specs', () => {
    templates.forEach(template => {
      expect(isDraftSpec(template.defaultSpec)).toBe(true);
      expect(template.defaultSpec.payload).toBeDefined();
    });
  });

  it('should include chatbot template', () => {
    expect(chatbotTemplate.id).toBe('chatbot');
    expect(chatbotTemplate.category).toBe('chatbot');
    expect(chatbotTemplate.interview).toBeDefined();
  });

  it('should include web automation template', () => {
    expect(webAutomationTemplate.id).toBe('web-automation');
    expect(webAutomationTemplate.category).toBe('web-automation');
  });

  it('should include API copilot template', () => {
    expect(apiCopilotTemplate.id).toBe('api-copilot');
    expect(apiCopilotTemplate.category).toBe('api-copilot');
  });
});
