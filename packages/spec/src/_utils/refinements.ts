import { z } from "zod";

export const kebabCase = () =>
  z
    .string()
    .min(1)
    .max(64)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);

// Basic ULID validation (26 Crockford base32 chars, no I,L,O,U)
export const ulid = () =>
  z
    .string()
    .length(26)
    .regex(/^[0-9A-HJKMNP-TV-Z]{26}$/);

export const isoDateString = () =>
  z
    .string()
    .refine((s) => !Number.isNaN(Date.parse(s)), { message: "Invalid ISO date" });
