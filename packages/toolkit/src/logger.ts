import pino from "pino";

export const logger = pino({
  transport:
    process.env.NODE_ENV === "development"
      ? { target: "pino-pretty", options: { colorize: true } }
      : undefined,
  redact: ["req.headers.authorization", "SESSION_SECRET_DEV"],
});
