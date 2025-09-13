# Spec Editor Implementation

This document describes the implementation of the UI Spec Panel with live validation for Week 2.

## Overview

The Spec Editor provides an in-browser Monaco-based editor for authoring Agent specifications with:
- Live validation using Zod schemas
- JSON/YAML toggle support
- Import/export functionality
- Draft persistence with RLS
- Template-based spec creation

## Architecture

### Database Layer
- **Migration**: `002_spec_drafts.sql` creates the `spec_drafts` table
- **Schema**: Drizzle ORM models in `packages/db/src/index.ts`
- **RLS**: Row-level security policies ensure users only see their own drafts

### API Layer
- **Route**: `apps/web/app/routes/api.specs.drafts.ts`
- **Operations**: CRUD for drafts (create, read, update, delete)
- **Validation**: Server-side Zod validation before persistence

### UI Components
- **SpecEditor**: Monaco-based editor with live validation worker
- **ValidationPanel**: Displays validation errors with click-to-focus
- **Drafts Catalog**: Grid view of user's saved drafts

### Pages/Routes
- `/specs/new` - Create new spec (with optional template)
- `/specs/:id` - Edit existing draft
- `/catalog/drafts` - List all user drafts

## Features Implemented

### ✅ Core Editor
- Monaco editor with JSON/YAML toggle
- Syntax highlighting and basic autocomplete
- JSON Schema integration for IntelliSense

### ✅ Live Validation
- Web Worker-based Zod validation (non-blocking)
- Real-time error highlighting with Monaco markers
- Debounced validation (300ms) for performance

### ✅ Draft Management
- Save/update drafts to PostgreSQL
- List drafts with metadata (name, tags, timestamps)
- Delete drafts with confirmation

### ✅ Import/Export
- File upload for JSON/YAML specs
- Export drafts as JSON files
- Size limits (200KB) for security

### ✅ Templates
- Predefined templates: chatbot, web-automation, api-copilot
- Template selection via URL parameter
- Pre-populated specs with valid examples

### ✅ User Experience
- Keyboard shortcuts (Ctrl/Cmd+S for save)
- Format button using Prettier
- Dirty state tracking with visual indicator
- Loading states and error handling

## Testing

### Unit Tests
- Zod validation logic
- JSON schema generation
- API route handlers

### Integration Tests  
- Draft CRUD operations
- Template loading
- Error handling

### E2E Tests (Future)
- Complete user flows
- Validation UX
- Cross-browser compatibility

## Security

### Input Validation
- Server-side Zod schema validation
- File size limits (200KB)
- JSON/YAML parse error handling

### Access Control
- Row-level security (RLS) on spec_drafts table
- User isolation via PostgreSQL policies
- Session-based authentication (mock for now)

## Performance

### Client-side
- Web Worker validation (non-blocking UI)
- Debounced validation to reduce CPU usage
- Code splitting for Monaco editor bundle

### Server-side
- Indexed database queries
- Efficient JSON handling with PostgreSQL jsonb
- Connection pooling via Drizzle ORM

## Next Steps (Future Work)

1. **Authentication Integration**: Replace mock auth with real user sessions
2. **Advanced Features**: Spec versioning, collaboration, comments
3. **Builder Integration**: Connect editor to Week 2 builder nodes
4. **Performance**: Optimize bundle size, add virtualization for large drafts
5. **A11y**: Screen reader support, high contrast mode
6. **Mobile**: Responsive design for tablet/mobile editing

## Files Added/Modified

### Database
- `packages/db/migrations/002_spec_drafts.sql`
- `packages/db/src/index.ts` (schema updates)

### API Routes
- `apps/web/app/routes/api.specs.drafts.ts`

### Components  
- `apps/web/app/components/SpecEditor.tsx`
- `apps/web/app/components/ValidationPanel.tsx`

### Pages
- `apps/web/app/routes/specs.new.tsx`
- `apps/web/app/routes/specs.$id.tsx` 
- `apps/web/app/routes/catalog.drafts.tsx`

### Utilities
- `apps/web/app/utils/schema.ts`
- `apps/web/app/workers/validation-worker.ts`

### Styles
- `apps/web/app/styles/spec-editor.css`

### Tests
- `apps/web/test/spec-editor.test.ts`
- `apps/web/test/setup.ts`
- `apps/web/vitest.config.ts`

### Config
- `apps/web/package.json` (dependencies)
- `apps/web/app/root.tsx` (navigation, styles)

## Acceptance Criteria Met

✅ **User can save a draft spec and see it in My Catalog as Draft**
- Drafts persist to PostgreSQL with RLS
- Catalog page lists all user drafts with metadata

✅ **Live validation highlights issues as the user types**
- Web Worker validation with Monaco markers
- Real-time error panel with click-to-focus
- Debounced for performance (300ms)

The implementation successfully delivers the Week 2 Spec Panel requirements with room for future enhancements.
