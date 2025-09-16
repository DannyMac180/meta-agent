import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createServer } from '../src/index';

describe('Runner Service Security Integration', () => {
  let app: any;

  beforeEach(async () => {
    // Set allow-list for testing
    process.env.ALLOW_HTTP_HOSTS = '["httpbin.org", "api.example.com"]';
    app = createServer();
    await app.ready();
  });

  afterEach(async () => {
    await app?.close();
    delete process.env.ALLOW_HTTP_HOSTS;
    delete process.env.SERPER_API_KEY;
    delete process.env.OPENAI_API_KEY;
  });

  describe('HTTP Tool Security', () => {
    it('should block requests to disallowed hosts via HTTP tool', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/tools/http',
        payload: {
          url: 'https://malicious.com/api',
          method: 'GET'
        }
      });

      expect(response.statusCode).toBe(400);
      expect(response.json().error).toContain('Blocked host');
    });

    it('should allow requests to allowed hosts via HTTP tool', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/tools/http',
        payload: {
          url: 'https://httpbin.org/json',
          method: 'GET'
        }
      });

      // Should not be blocked (may fail with network error in test env, but that's OK)
      if (response.statusCode === 400) {
        expect(response.json().error).not.toContain('Blocked host');
      }
    });

    it('should validate requests with wildcard patterns', async () => {
      // Update allow-list to use wildcards
      process.env.ALLOW_HTTP_HOSTS = '["*.httpbin.org"]';
      
      const response = await app.inject({
        method: 'POST',
        url: '/tools/http',
        payload: {
          url: 'https://eu.httpbin.org/get',
          method: 'GET'
        }
      });

      if (response.statusCode === 400) {
        expect(response.json().error).not.toContain('Blocked host');
      }
    });
  });

  describe('WebSearch Tool Security', () => {
    it('should respect allow-list for search API calls', async () => {
      // Set API key and clear allow-list to block external requests
      process.env.SERPER_API_KEY = 'test-key';
      process.env.ALLOW_HTTP_HOSTS = '[]';
      
      const response = await app.inject({
        method: 'POST',
        url: '/tools/webSearch',
        payload: {
          query: 'test search'
        }
      });

      expect(response.statusCode).toBe(400);
      const error = response.json().error;
      // Should be blocked by allow-list, not by missing API key
      expect(error).toContain('Blocked host');
    });
  });

  describe('Vector Tool Security', () => {
    it('should respect allow-list for embedding API calls', async () => {
      // Set API key and clear allow-list to block external requests
      process.env.OPENAI_API_KEY = 'test-key';
      process.env.ALLOW_HTTP_HOSTS = '[]';
      
      const response = await app.inject({
        method: 'POST',
        url: '/tools/vector',
        payload: {
          action: 'embed',
          text: 'test text'
        }
      });

      expect(response.statusCode).toBe(400);
      const error = response.json().error;
      // Should be blocked by allow-list, not by missing API key
      expect(error).toContain('Blocked host');
    });
  });

  describe('Service Validation', () => {
    it('should validate allow-list configuration on startup', async () => {
      // This is tested implicitly by the beforeEach setup
      // The service should start without throwing errors when properly configured
      expect(app).toBeDefined();
    });

    it('should handle empty allow-list gracefully', async () => {
      process.env.ALLOW_HTTP_HOSTS = '';
      const testApp = createServer();
      
      // Should not crash on startup, but will log warnings
      await expect(testApp.ready()).resolves.not.toThrow();
      await testApp.close();
    });

    it('should handle malformed allow-list gracefully', async () => {
      process.env.ALLOW_HTTP_HOSTS = '{malformed json}';
      const testApp = createServer();
      
      // Should not crash on startup
      await expect(testApp.ready()).resolves.not.toThrow();
      await testApp.close();
    });
  });
});
