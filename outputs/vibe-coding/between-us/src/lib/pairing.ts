import { createHash, randomBytes } from "crypto";

export type Response = { thought: string; outward: string; wish: string };

export function hashSecret(value: string) {
  return createHash("sha256").update(value).digest("hex");
}

export function normalizeShareCode(value: string) {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, "");
}

export function makeShareCode() {
  const raw = randomBytes(18).toString("base64url").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 24);
  return raw.match(/.{1,4}/g)?.join("-") ?? raw;
}

export function makeSessionCode() {
  const raw = randomBytes(12).toString("base64url").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
  return raw.match(/.{1,4}/g)?.join("-") ?? raw;
}

export function makeAccessToken() {
  return randomBytes(32).toString("base64url");
}

export function isResponse(value: unknown): value is Response {
  if (!value || typeof value !== "object") return false;
  const response = value as Record<string, unknown>;
  return ["thought", "outward", "wish"].every((key) => {
    const text = response[key];
    return typeof text === "string" && text.trim().length > 0 && text.length <= 240;
  });
}

export function isDraftResponse(value: unknown): value is Response {
  if (!value || typeof value !== "object") return false;
  const response = value as Record<string, unknown>;
  return ["thought", "outward", "wish"].every((key) => {
    const text = response[key];
    return typeof text === "string" && text.length <= 240;
  });
}

export function cleanName(value: unknown) {
  return typeof value === "string" ? value.trim().slice(0, 16) : "";
}

export function cleanCardId(value: unknown) {
  return typeof value === "string" && /^[a-z0-9-]{3,32}$/.test(value) ? value : "";
}
