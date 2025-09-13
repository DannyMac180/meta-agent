import { vi } from "vitest";

// Mock fetch for tests
Object.defineProperty(window, 'fetch', {
  writable: true,
  value: vi.fn(),
});

// Mock Monaco editor
Object.defineProperty(window, 'monaco', {
  writable: true,
  value: {
    editor: {
      setModelMarkers: vi.fn(),
    },
    languages: {
      json: {
        jsonDefaults: {
          setDiagnosticsOptions: vi.fn()
        }
      }
    },
    KeyMod: {
      CtrlCmd: 1,
      Shift: 2
    },
    KeyCode: {
      KeyS: 1,
      KeyF: 2
    },
    MarkerSeverity: {
      Error: 1
    }
  },
});

// Mock Web Workers
Object.defineProperty(window, 'Worker', {
  writable: true,
  value: vi.fn().mockImplementation(() => ({
    postMessage: vi.fn(),
    terminate: vi.fn(),
    onmessage: null
  }))
});
