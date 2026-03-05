<template>
  <div>
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="font-sans text-3xl font-bold text-gray-900">
        Мои карусели
      </h1>
      <NuxtLink
        to="/create"
        class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90"
      >
        Создать карусель
      </NuxtLink>
    </div>

    <div v-if="pending && !items.length" class="text-gray-500">
      Загрузка…
    </div>

    <div
      v-else-if="error"
      class="rounded-lg border border-red-200 bg-red-50 py-12 text-center text-red-600"
    >
      {{ error }}
    </div>

    <div
      v-else-if="!items.length"
      class="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-12 text-center"
    >
      <div
        class="mb-4 flex gap-1 text-gray-300"
        aria-hidden="true"
      >
        <span class="h-14 w-10 rounded border border-gray-200 bg-gray-50" />
        <span class="h-16 w-11 rounded border border-gray-200 bg-gray-100" />
        <span class="h-14 w-10 rounded border border-gray-200 bg-gray-50" />
      </div>
      <h2 class="text-xl font-semibold text-gray-900">
        Создать карусель
      </h2>
      <p class="mt-1 max-w-sm text-sm text-gray-500">
        Покажем новое видео с каждого аккаунта в течение 24 часов
      </p>
      <NuxtLink
        to="/create"
        class="mt-6 inline-flex justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90"
      >
        + Создать
      </NuxtLink>
    </div>

    <div
      v-else
      class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <CarouselCard
        v-for="carousel in items"
        :key="carousel.id"
        :carousel="carousel"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CarouselListResponse } from "~/types/carousel";

const { request } = useApi();

const items = ref<CarouselListResponse["items"]>([]);
const pending = ref(true);
const error = ref<string | null>(null);
const fetching = ref(false);

let abortController: AbortController | null = null;

async function fetchList() {
  if (fetching.value) return;
  fetching.value = true;
  error.value = null;
  pending.value = true;

  abortController = new AbortController();

  try {
    const data = await request<CarouselListResponse>("/api/v1/carousels", {
      signal: abortController.signal,
    });
    items.value = data.items;
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    error.value = "Не удалось загрузить список каруселей";
  } finally {
    pending.value = false;
    fetching.value = false;
    abortController = null;
  }
}

const hasGenerating = computed(() =>
  items.value.some((c) => c.status === "generating")
);

let pollTimer: ReturnType<typeof setInterval> | null = null;

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(() => {
    if (!hasGenerating.value) {
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
      return;
    }
    fetchList();
  }, 5000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onMounted(() => {
  fetchList();
});

watch(hasGenerating, (val) => {
  if (val) startPolling();
  else stopPolling();
}, { immediate: true });

onUnmounted(() => {
  stopPolling();
  abortController?.abort();
});
</script>
