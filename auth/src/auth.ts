import { betterAuth } from "better-auth";
import bcrypt from "bcrypt";
import pg from "pg";
import { Resend } from "resend";

const { Pool } = pg;

const secret = process.env.BETTER_AUTH_SECRET;
if (!secret) {
  throw new Error("BETTER_AUTH_SECRET environment variable is required");
}

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  console.warn(
    "WARNING: DATABASE_URL is not set — using default localhost connection. " +
    "Set DATABASE_URL for production deployments."
  );
}

export const pool = new Pool({
  connectionString: databaseUrl ?? "postgresql://cartsnitch:cartsnitch@localhost:5432/cartsnitch",
});

const resend = new Resend(process.env.RESEND_API_KEY);
const fromEmail = process.env.FROM_EMAIL || "CartSnitch <noreply@cartsnitch.com>";

export const auth = betterAuth({
  database: pool,
  basePath: "/auth",
  secret,
  baseURL: process.env.BETTER_AUTH_URL ?? "http://localhost:3001",

  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
    password: {
      hash: async (password: string) => {
        return bcrypt.hash(password, 12);
      },
      verify: async (data: { hash: string; password: string }) => {
        return bcrypt.compare(data.password, data.hash);
      },
    },
  },

  emailVerification: {
    sendOnSignUp: true,
    autoSignInAfterVerification: true,
    sendVerificationEmail: async ({ user, url }) => {
      await resend.emails.send({
        from: fromEmail,
        to: user.email,
        subject: "Verify your CartSnitch email",
        html: `<p>Hi ${user.name || ""},</p><p>Click the link below to verify your email address:</p><p><a href="${url}">Verify Email</a></p><p>This link expires in 1 hour.</p><p>— CartSnitch</p>`,
      });
    },
  },

  session: {
    modelName: "sessions",
    fields: {
      userId: "user_id",
      expiresAt: "expires_at",
      ipAddress: "ip_address",
      userAgent: "user_agent",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // refresh after 1 day
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60, // 5-minute cookie cache
    },
  },

  user: {
    modelName: "users",
    fields: {
      name: "display_name",
      emailVerified: "email_verified",
      image: "image",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },

  account: {
    modelName: "accounts",
    fields: {
      userId: "user_id",
      accountId: "account_id",
      providerId: "provider_id",
      accessToken: "access_token",
      refreshToken: "refresh_token",
      accessTokenExpiresAt: "access_token_expires_at",
      refreshTokenExpiresAt: "refresh_token_expires_at",
      idToken: "id_token",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },

  verification: {
    modelName: "verifications",
    fields: {
      expiresAt: "expires_at",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },

  trustedOrigins: [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://cartsnitch.com",
    "https://cartsnitch.farh.net",
    "https://cartsnitch.dev.farh.net",
    "https://cartsnitch.uat.farh.net",
  ],
});