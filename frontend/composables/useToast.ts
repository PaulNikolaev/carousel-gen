let hideTimeout: ReturnType<typeof setTimeout> | null = null;

export function useToast() {
  const message = useState<string>("toast-message", () => "");
  const isVisible = useState<boolean>("toast-visible", () => false);

  function showError(msg: string) {
    if (import.meta.server) return;
    if (hideTimeout) clearTimeout(hideTimeout);
    message.value = msg;
    isVisible.value = true;
    hideTimeout = setTimeout(() => {
      isVisible.value = false;
      hideTimeout = null;
    }, 5000);
  }

  function clear() {
    if (import.meta.server) return;
    if (hideTimeout) clearTimeout(hideTimeout);
    hideTimeout = null;
    isVisible.value = false;
    message.value = "";
  }

  return { message, isVisible, showError, clear };
}
