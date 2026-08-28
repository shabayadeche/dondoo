import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().default(4000),
  DATABASE_URL: z
    .string()
    .default("postgresql://postgres:postgres@localhost:5432/phd_ass"),
  ALLOW_ORIGIN: z.string().default("*"),
  ODOO_BRIDGE_API_KEY: z.string().default("")
});

export const env = envSchema.parse(process.env);
