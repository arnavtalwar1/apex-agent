/** Accept only same-origin paths when returning from authentication. */
export function safeRedirect(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || /[\\\x00-\x1f]/.test(value)) return "/";
  try {
    const url = new URL(value, "https://apex.invalid");
    return url.origin === "https://apex.invalid" ? url.pathname + url.search + url.hash : "/";
  } catch { return "/"; }
}
