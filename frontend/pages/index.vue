<template>
  <div>
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-3xl font-bold text-gray-900">
        Мои карусели
      </h1>
      <NuxtLink
        to="/create"
        class="inline-flex justify-center rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gray-800"
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
      class="rounded-lg border border-gray-200 bg-white py-12 text-center text-gray-500"
    >
      Каруселей пока нет. Создайте первую.
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

definePageMeta({
  layout: "default",
});

const { request } = useApi();

const items = ref<CarouselListResponse["items"]>([]);
const pending = ref(true);
const error = ref<string | null>(null);
const fetching = ref(false);

async function fetchList() {
  if (fetching.value) return;
  fetching.value = true;
  error.value = null;
  pending.value = true;
  try {
    const data = await request<CarouselListResponse>("/api/v1/carousels");
    items.value = data.items;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Ошибка загрузки";
  } finally {
    pending.value = false;
    fetching.value = false;
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
});
</script>
