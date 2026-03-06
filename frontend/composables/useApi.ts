import type { FetchError } from "ofetch";

export function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = (
    (config.public.apiBaseUrl as string) ||
    "http://localhost:8000"
  ).replace(/\/$/, "");
  const apiKey = (config.public.apiKey as string) || "";
  const toast = useToast();

  async function request<T>(
    path: string,
    options?: Parameters<typeof $fetch<unknown>>[1]
  ): Promise<T> {
    const url = path.startsWith("/") ? `${baseUrl}${path}` : `${baseUrl}/${path}`;
    const headers = {
      ...(options?.headers as Record<string, string> | undefined),
      ...(apiKey ? { "X-API-Key": apiKey } : {}),
    };
    try {
      return await $fetch<T>(url, { ...options, headers });
    } catch (e: unknown) {
      const err = e as FetchError;
      const detail = (err as { data?: { detail?: unknown } }).data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? (detail as Array<{ msg: string } | string>)
                .map((item) => (typeof item === "string" ? item : item.msg))
                .join(", ")
            : err?.message ?? "Ошибка запроса";
      toast.showError(msg);
      throw e;
    }
  }

  return { request };
}
