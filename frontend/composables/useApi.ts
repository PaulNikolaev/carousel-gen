export function useApi() {
  const config = useRuntimeConfig();
  const baseUrl = ((config.public.apiBaseUrl as string) || "http://localhost:8000").replace(/\/$/, "");
  const toast = useToast();

  async function request<T>(
    path: string,
    options?: Parameters<typeof $fetch<unknown>>[1]
  ): Promise<T> {
    const url = path.startsWith("/") ? `${baseUrl}${path}` : `${baseUrl}/${path}`;
    try {
      return await $fetch<T>(url, options);
    } catch (e: unknown) {
      const err = e as { data?: { detail?: string }; message?: string };
      const msg =
        typeof err?.data?.detail === "string"
          ? err.data.detail
          : Array.isArray(err?.data?.detail)
            ? (err.data.detail as Array<{ msg: string } | string>)
                .map((item) => (typeof item === "string" ? item : item.msg))
                .join(", ")
            : err?.message ?? "Ошибка запроса";
      toast.showError(msg);
      throw e;
    }
  }

  return { request };
}
