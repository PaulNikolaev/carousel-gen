<template>
  <div>
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="font-sans text-3xl font-bold text-gray-900">
        Мои карусели
      </h1>
      <NuxtLink
        to="/create"
        class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        aria-label="Создать новую карусель"
      >
        Создать карусель
      </NuxtLink>
    </div>

    <div
      v-if="pending && !items.length"
      role="status"
      aria-label="Загрузка списка каруселей"
      class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <div
        v-for="i in 3"
        :key="i"
        class="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
      >
        <div class="aspect-[4/5] w-full shrink-0 animate-pulse bg-gray-200" />
        <div class="flex flex-1 flex-col p-6">
          <div class="h-5 w-3/4 animate-pulse rounded bg-gray-200" />
          <div class="mt-2 h-4 w-1/3 animate-pulse rounded bg-gray-100" />
          <div class="mt-2 flex gap-2">
            <span class="h-5 w-16 animate-pulse rounded-full bg-gray-100" />
            <span class="h-4 w-20 animate-pulse rounded bg-gray-100" />
          </div>
          <div class="mt-4 h-10 w-full animate-pulse rounded-md bg-gray-200" />
        </div>
      </div>
    </div>

    <div
      v-else-if="error"
      role="alert"
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
        Пока нет каруселей
      </h2>
      <p class="mt-1 max-w-sm text-sm text-gray-700">
        Создайте первую карусель
      </p>
      <NuxtLink
        to="/create"
        class="mt-6 inline-flex justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        aria-label="Создать первую карусель"
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
        :deleting-id="deletingCarouselId"
        @delete="onDeleteCarousel"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CarouselListResponse } from "~/types/carousel";

const { request } = useApi();

const items = ref<CarouselListResponse["items"]>([]);
const pending = ref(false);
const error = ref<string | null>(null);
const deletingCarouselId = ref<string | null>(null);

let abortController: AbortController | null = null;

async function fetchList() {
  if (pending.value) return;
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
    abortController = null;
  }
}

async function onDeleteCarousel(id: string) {
  if (!confirm("Удалить эту карусель? Действие нельзя отменить.")) return;
  deletingCarouselId.value = id;
  try {
    await request(`/api/v1/carousels/${id}`, { method: "DELETE" });
    items.value = items.value.filter((c) => c.id !== id);
  } finally {
    deletingCarouselId.value = null;
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
