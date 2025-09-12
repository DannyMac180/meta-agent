import type { RedisOptions } from "ioredis";

function fromEnv(): RedisOptions {
  const urlStr = process.env.REDIS_URL ?? "redis://localhost:6379";
  const u = new URL(urlStr);
  const password = u.password || undefined;
  const host = u.hostname || "localhost";
  const port = u.port ? Number(u.port) : 6379;
  return {
    host,
    port,
    password,
    maxRetriesPerRequest: null,
    enableReadyCheck: true,
  } as RedisOptions;
}

export const redisOptions: RedisOptions = fromEnv();
