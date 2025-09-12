import type { Config } from 'drizzle-kit';

export default {
  schema: './docs/data_model.sql',
  driver: 'pg',
  dbCredentialsEnv: {
    connectionString: 'DATABASE_URL',
  },
  out: './packages/db/migrations',
} satisfies Config;
