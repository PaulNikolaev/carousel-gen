<template>
  <div class="font-sans tracking-[-0.025em]" style="font-size: 13.5px;">
    <nav aria-label="Хлебные крошки" class="mb-4 flex items-center gap-2 text-gray-600">
      <NuxtLink to="/" class="transition-colors hover:text-primary">
        Карусели
      </NuxtLink>
      <span aria-hidden="true">/</span>
      <span class="text-gray-900">{{ carousel?.title || `Карусель ${id}` }}</span>
    </nav>

    <div v-if="loadError" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-600">
      {{ loadError }}
    </div>

    <template v-else-if="carousel">
      <!-- Draft: trigger generation -->
      <template v-if="viewMode === 'draft'">
        <h1 class="mb-2 text-2xl font-bold text-gray-900">
          Генерация карусели
        </h1>
        <p class="mb-4 text-gray-600">
          Слайды ещё не сгенерированы. Нажмите кнопку, чтобы запустить генерацию.
        </p>
        <p v-if="tokensEstimate !== null" class="mb-4 text-gray-600">
          При генерации будет списано ориентировочно {{ tokensEstimate }} токенов.
        </p>
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-white shadow-sm transition-colors hover:bg-primary/90 disabled:opacity-50"
          :disabled="starting"
          @click="startGeneration"
        >
          {{ starting ? "Запуск…" : "Сгенерировать" }}
        </button>
      </template>

      <!-- Progress: queued / running (with optional generation_id from POST) or carousel.status=generating -->
      <template v-else-if="viewMode === 'progress'">
        <h1 class="mb-2 text-2xl font-bold text-gray-900">
          Генерация
        </h1>
        <div class="flex items-center gap-3">
          <span
            class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"
            aria-hidden="true"
          />
          <span class="text-gray-700">
            {{ progressStatusText }}
          </span>
        </div>
        <p v-if="tokensEstimate !== null" class="mt-2 text-gray-600">
          Спишется ориентировочно {{ tokensEstimate }} токенов.
        </p>
      </template>

      <!-- Failed: message + Retry -->
      <template v-else-if="viewMode === 'failed'">
        <h1 class="mb-2 text-2xl font-bold text-gray-900">
          Ошибка генерации
        </h1>
        <p class="mb-4 text-gray-600">
          {{ failedMessage }}
        </p>
        <button
          type="button"
          class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-white shadow-sm transition-colors hover:bg-primary/90"
          @click="startGeneration"
        >
          Повторить
        </button>
      </template>

      <!-- Editor placeholder (ready) -->
      <template v-else-if="viewMode === 'editor'">
        <h1 class="mb-4 text-2xl font-bold text-gray-900">
          Редактор
        </h1>
        <div class="flex flex-col gap-4">
          <p v-if="editorSlidesLoading" class="text-gray-500">
            Загрузка слайдов…
          </p>
          <template v-else>
            <p class="text-gray-600">
              Слайды ({{ editorSlides.length }}):
            </p>
            <ul class="list-inside list-disc space-y-1 text-gray-700">
              <li v-for="s in editorSlides" :key="s.order">
                {{ s.title || `Слайд ${s.order}` }}
              </li>
            </ul>
          </template>
        </div>
      </template>
    </template>

    <div v-else-if="!carousel && !loadError" class="text-gray-500">
      Загрузка…
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CarouselResponse } from "~/types/carousel";
import type {
  GenerationResponse,
  GenerationSlideItem,
  StartGenerationResponse,
} from "~/types/generation";

definePageMeta({ layout: "default" });

const route = useRoute();
const id = computed(() => route.params.id as string);

const { request } = useApi();

const carousel = ref<CarouselResponse | null>(null);
const loadError = ref<string | null>(null);
const starting = ref(false);
const tokensEstimate = ref<number | null>(null);
const activeGenerationId = ref<string | null>(null);
const generation = ref<GenerationResponse | null>(null);
const editorSlides = ref<GenerationSlideItem[]>([]);
const editorSlidesLoading = ref(false);

const POLL_INTERVAL_MS = 3000;
let pollTimer: ReturnType<typeof setInterval> | null = null;

type ViewMode = "draft" | "progress" | "failed" | "editor";

const viewMode = computed<ViewMode>(() => {
  if (!carousel.value) return "draft";
  const status = carousel.value.status;
  if (status === "ready") return "editor";
  if (status === "failed") return "failed";
  if (status === "generating" || generation.value) {
    const genStatus = generation.value?.status;
    if (genStatus === "failed") return "failed";
    if (genStatus === "done") return "editor";
    return "progress";
  }
  return "draft";
});

const progressStatusText = computed(() => {
  const s = generation.value?.status;
  if (s === "queued") return "В очереди…";
  return "Генерация…";
});

const failedMessage = computed(() => {
  return generation.value?.error_message || "Генерация не удалась.";
});

async function fetchCarousel() {
  loadError.value = null;
  try {
    carousel.value = await request<CarouselResponse>(
      `/api/v1/carousels/${id.value}`
    );
  } catch {
    loadError.value = "Карусель не найдена.";
    carousel.value = null;
  }
}

async function startGeneration() {
  if (starting.value) return;
  starting.value = true;
  tokensEstimate.value = null;
  generation.value = null;
  try {
    const data = await request<StartGenerationResponse>("/api/v1/generations", {
      method: "POST",
      body: { carousel_id: id.value },
    });
    activeGenerationId.value = data.generation_id;
    tokensEstimate.value = data.tokens_estimate;
    await fetchCarousel();
    startPollingGeneration();
  } catch {
    // useApi shows toast
  } finally {
    starting.value = false;
  }
}

async function pollGeneration() {
  if (!activeGenerationId.value) return;
  try {
    const gen = await request<GenerationResponse>(
      `/api/v1/generations/${activeGenerationId.value}`
    );
    generation.value = gen;
    if (gen.status === "done" && gen.result?.length) {
      editorSlides.value = [...gen.result];
      stopPolling();
      await fetchCarousel();
    } else if (gen.status === "failed") {
      stopPolling();
      await fetchCarousel();
    }
    if (gen.tokens_estimate != null) tokensEstimate.value = gen.tokens_estimate;
  } catch {
    // keep polling on transient errors
  }
}

function startPollingGeneration() {
  stopPolling();
  pollTimer = setInterval(pollGeneration, POLL_INTERVAL_MS);
  pollGeneration();
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function ensureEditorSlides() {
  if (editorSlides.value.length) return;
  editorSlidesLoading.value = true;
  try {
    const slides = await request<GenerationSlideItem[]>(
      `/api/v1/carousels/${id.value}/slides`
    );
    editorSlides.value = slides;
  } catch {
    // keep empty
  } finally {
    editorSlidesLoading.value = false;
  }
}

watch(
  () => viewMode.value,
  (mode) => {
    if (mode === "editor") ensureEditorSlides();
  },
  { immediate: true }
);

watch(
  () => carousel.value?.status,
  (status) => {
    if (status === "generating" && !activeGenerationId.value) {
      // Refreshed during generation: poll carousel until ready/failed
      startCarouselPolling();
    } else {
      stopCarouselPolling();
    }
  }
);

let carouselPollTimer: ReturnType<typeof setInterval> | null = null;

function startCarouselPolling() {
  if (carouselPollTimer) return;
  carouselPollTimer = setInterval(async () => {
    await fetchCarousel();
    const s = carousel.value?.status;
    if (s === "ready") {
      stopCarouselPolling();
      await ensureEditorSlides();
    } else if (s === "failed") {
      stopCarouselPolling();
    }
  }, POLL_INTERVAL_MS);
}

function stopCarouselPolling() {
  if (carouselPollTimer) {
    clearInterval(carouselPollTimer);
    carouselPollTimer = null;
  }
}

onMounted(() => {
  fetchCarousel();
});

onUnmounted(() => {
  stopPolling();
  stopCarouselPolling();
});
</script>
