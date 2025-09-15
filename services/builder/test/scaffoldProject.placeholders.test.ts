import { describe, it, expect, beforeAll } from 'vitest';
import Handlebars from 'handlebars';

describe('Placeholder Engine', () => {
  beforeAll(() => {
    // Register helpers like scaffoldProject.ts does
    Handlebars.registerHelper("default", function (this: any, value: any, def: any) {
      return value != null && value !== "" ? value : def;
    });
    Handlebars.registerHelper("upper", function (this: any, value: any) {
      return typeof value === "string" ? value.toUpperCase() : value;
    });
    Handlebars.registerHelper("json", function (this: any, value: any) {
      return new Handlebars.SafeString(JSON.stringify(value ?? null));
    });
    Handlebars.registerHelper("slugify", function (this: any, value: any) {
      return String(value ?? "")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
    });
  });

  it('renders basic placeholders', () => {
    const template = Handlebars.compile('Hello {{name}}!');
    const result = template({ name: 'World' });
    expect(result).toBe('Hello World!');
  });

  it('renders nested property access', () => {
    const template = Handlebars.compile('Name: {{meta.name}}');
    const result = template({ meta: { name: 'my-app' } });
    expect(result).toBe('Name: my-app');
  });

  it('uses default helper for missing values', () => {
    const template = Handlebars.compile('{{default meta.version "1.0.0"}}');
    
    // With value present
    const result1 = template({ meta: { version: '2.0.0' } });
    expect(result1).toBe('2.0.0');
    
    // With value missing
    const result2 = template({ meta: {} });
    expect(result2).toBe('1.0.0');
    
    // With null/empty value
    const result3 = template({ meta: { version: '' } });
    expect(result3).toBe('1.0.0');
  });

  it('uses upper helper', () => {
    const template = Handlebars.compile('{{upper name}}');
    const result = template({ name: 'hello world' });
    expect(result).toBe('HELLO WORLD');
  });

  it('uses json helper', () => {
    const template = Handlebars.compile('Config: {{json config}}');
    const result = template({ config: { debug: true, port: 3000 } });
    expect(result).toBe('Config: {"debug":true,"port":3000}');
  });

  it('uses slugify helper', () => {
    const template = Handlebars.compile('{{slugify title}}');
    
    const result1 = template({ title: 'My Amazing Project!' });
    expect(result1).toBe('my-amazing-project');
    
    const result2 = template({ title: 'Café & Restaurant   App' });
    expect(result2).toBe('cafe-restaurant-app');
  });

  it('renders realistic package.json template', () => {
    const template = Handlebars.compile(`{
  "name": "{{meta.name}}",
  "version": "{{default meta.version "1.0.0"}}",
  "description": "{{default meta.description "Generated agent"}}",
  "private": true
}`);
    
    const context = {
      meta: {
        name: 'my-chatbot',
        description: 'A helpful assistant'
      }
    };
    
    const result = template(context);
    const parsed = JSON.parse(result);
    
    expect(parsed.name).toBe('my-chatbot');
    expect(parsed.version).toBe('1.0.0');
    expect(parsed.description).toBe('A helpful assistant');
    expect(parsed.private).toBe(true);
  });

  it('renders README template with variables', () => {
    const template = Handlebars.compile(`# {{title}}

{{default meta.description "A generated agent"}}

{{#if variables}}
## Variables

{{#each variables}}
- {{name}} ({{key}}) - {{description}}
{{/each}}
{{/if}}`);

    const context = {
      title: 'Weather Agent',
      meta: { description: 'Gets weather information' },
      variables: [
        { key: 'location', name: 'Location', description: 'The city to get weather for' },
        { key: 'units', name: 'Units', description: 'Temperature units (F or C)' }
      ]
    };

    const result = template(context);
    expect(result).toContain('# Weather Agent');
    expect(result).toContain('Gets weather information');
    expect(result).toContain('- Location (location) - The city to get weather for');
    expect(result).toContain('- Units (units) - Temperature units (F or C)');
  });
});
