import { describe, it, expect, beforeEach, vi } from 'vitest';
import { safeFetch, validateAllowList } from '../src/client';

describe('Security: Egress Allow-List Enforcement', () => {
  beforeEach(() => {
    // Clear environment before each test
    delete process.env.ALLOW_HTTP_HOSTS;
  });

  describe('validateAllowList', () => {
    it('should fail when ALLOW_HTTP_HOSTS is empty', () => {
      const result = validateAllowList();
      expect(result.isValid).toBe(false);
      expect(result.error).toContain('empty');
    });

    it('should pass with valid JSON array', () => {
      process.env.ALLOW_HTTP_HOSTS = '["api.example.com", "*.trusted.com"]';
      const result = validateAllowList();
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should pass with comma-separated hosts', () => {
      process.env.ALLOW_HTTP_HOSTS = 'api.example.com, *.trusted.com';
      const result = validateAllowList();
      expect(result.isValid).toBe(true);
    });

    it('should fail with empty JSON array', () => {
      process.env.ALLOW_HTTP_HOSTS = '[]';
      const result = validateAllowList();
      expect(result.isValid).toBe(false);
      expect(result.error).toContain('empty');
    });

    it('should fail with invalid JSON', () => {
      process.env.ALLOW_HTTP_HOSTS = '{"invalid": "object"}';
      const result = validateAllowList();
      expect(result.isValid).toBe(false);
      expect(result.error).toContain('must be an array');
    });

    it('should fail with invalid host pattern', () => {
      process.env.ALLOW_HTTP_HOSTS = '["valid.com", "", "another.com"]';
      const result = validateAllowList();
      expect(result.isValid).toBe(false);
      expect(result.error).toContain('Invalid host pattern');
    });
  });

  describe('safeFetch blocking', () => {
    it('should block all requests when allow-list is empty', async () => {
      process.env.ALLOW_HTTP_HOSTS = '';
      await expect(
        safeFetch({ url: 'https://google.com' })
      ).rejects.toThrow('Blocked host: google.com');
    });

    it('should block disallowed hosts', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["api.example.com"]';
      await expect(
        safeFetch({ url: 'https://malicious.com/api' })
      ).rejects.toThrow('Blocked host: malicious.com');
    });

    it('should allow exact host matches', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["httpbin.org"]';
      
      // Should not be blocked - either succeeds or fails with network error
      try {
        const result = await safeFetch({ url: 'https://httpbin.org/get' });
        // If it succeeds, that's fine - it wasn't blocked
        expect(result).toBeDefined();
      } catch (error: any) {
        // If it fails, make sure it's NOT because of blocking
        expect(error.message).not.toContain('Blocked host');
      }
    });

    it('should support wildcard patterns', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["*.example.com"]';
      
      // Should be blocked - not matching pattern
      await expect(
        safeFetch({ url: 'https://malicious.com' })
      ).rejects.toThrow('Blocked host: malicious.com');
      
      // Should be allowed - matches wildcard (either succeeds or fails with network error)
      try {
        await safeFetch({ url: 'https://api.example.com/data' });
      } catch (error: any) {
        expect(error.message).not.toContain('Blocked host');
      }
    });

    it('should enforce timeouts', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["httpbin.org"]';
      
      await expect(
        safeFetch({ 
          url: 'https://httpbin.org/delay/5', 
          timeoutMs: 100 
        })
      ).rejects.toThrow('timed out');
    }, 10000);

    it('should log blocked requests', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["allowed.com"]';
      
      const originalWarn = console.warn;
      const warnSpy = vi.fn();
      console.warn = warnSpy;
      
      try {
        await expect(
          safeFetch({ url: 'https://blocked.com/path' })
        ).rejects.toThrow('Blocked host');
        
        expect(warnSpy).toHaveBeenCalledWith(
          expect.stringContaining('[SECURITY] Blocked HTTP request to disallowed host: blocked.com')
        );
      } finally {
        console.warn = originalWarn;
      }
    });
  });

  describe('Network isolation validation', () => {
    it('should prevent common bypass attempts', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["api.example.com"]';
      
      // Try various bypass techniques
      const bypassUrls = [
        'http://127.0.0.1:8080',      // localhost
        'http://10.0.0.1',            // private IP
        'http://169.254.169.254',     // metadata service
        'http://0.0.0.0',             // all interfaces
        'ftp://api.example.com',      // different protocol (should be blocked at URL parsing)
      ];
      
      for (const url of bypassUrls) {
        await expect(
          safeFetch({ url })
        ).rejects.toThrow();
      }
    });

    it('should handle malformed URLs gracefully', async () => {
      process.env.ALLOW_HTTP_HOSTS = '["api.example.com"]';
      
      const malformedUrls = [
        'not-a-url',
        'http://',
        'https://[invalid',
        'http://user:pass@host:99999999/path',
      ];
      
      for (const url of malformedUrls) {
        await expect(
          safeFetch({ url })
        ).rejects.toThrow(); // Should throw some error, either parsing or blocking
      }
    });
  });
});
