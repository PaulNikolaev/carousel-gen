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

      <!-- Editor: thumbnails | preview (4:5) | settings -->
      <template v-else-if="viewMode === 'editor'">
        <div class="mb-4 flex items-center justify-between gap-4">
          <h1 class="text-2xl font-bold text-gray-900">
            Редактор
          </h1>
          <NuxtLink
            to="/"
            class="text-accent font-medium transition-colors hover:text-accent/90"
          >
            Готово
          </NuxtLink>
        </div>
        <p v-if="editorSlidesLoading" class="text-gray-500">
          Загрузка слайдов…
        </p>
        <div
          v-else
          class="grid gap-4"
          style="grid-template-columns: minmax(0, 120px) minmax(0, 1fr) minmax(0, 280px);"
        >
          <!-- Left: thumbnails -->
          <div class="flex flex-col gap-2 overflow-y-auto">
            <button
              v-for="(s, idx) in editorSlides"
              :key="s.id"
              type="button"
              class="slide-thumb flex shrink-0 overflow-hidden rounded border-2 transition-colors"
              :class="currentSlideIndex === idx ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'"
              :aria-label="`Слайд ${s.order}`"
              :aria-pressed="currentSlideIndex === idx"
              style="aspect-ratio: 4/5; max-height: 120px;"
              @click="currentSlideIndex = idx"
            >
              <SlidePreview
                :slide="{ title: s.title, body: s.body, footer: s.footer }"
                :design="editorDesignThumb"
                :slide-index="s.order"
                :total-slides="editorSlides.length"
                class="!h-full !w-full !rounded-none !border-0"
              />
            </button>
          </div>
          <!-- Center: current slide preview (4:5) -->
          <div class="flex min-h-0 items-start justify-center">
            <div class="w-full max-w-md">
              <template v-if="currentSlide">
                <SlidePreview
                  :slide="{ title: currentSlide.title, body: currentSlide.body, footer: currentSlide.footer }"
                  :design="editorDesign"
                  :slide-index="currentSlide.order"
                  :total-slides="editorSlides.length"
                />
              </template>
            </div>
          </div>
          <!-- Right: design panel + slide edit fields -->
          <aside class="flex flex-col gap-4 rounded-lg border border-gray-200 bg-gray-50/50 p-4">
            <h2 class="text-sm font-semibold text-gray-900">
              Настройки
            </h2>
            <DesignPanel
              :design="editorDesign"
              @update="onDesignUpdate"
              @apply-to-all="onDesignApplyToAll"
            />
            <div class="border-t border-gray-200 pt-3">
              <h3 class="mb-2 text-xs font-semibold text-gray-700">
                Текст слайда
              </h3>
              <template v-if="currentSlide">
                <div class="flex flex-col gap-1">
                  <label for="edit-title" class="text-xs font-medium text-gray-600">Заголовок</label>
                  <textarea
                    id="edit-title"
                    :value="editTitle"
                    rows="2"
                    class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    @input="onEditTitle"
                  />
                </div>
                <div class="flex flex-col gap-1">
                  <label for="edit-body" class="text-xs font-medium text-gray-600">Текст</label>
                  <textarea
                    id="edit-body"
                    :value="editBody"
                    rows="4"
                    class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    @input="onEditBody"
                  />
                </div>
                <div class="flex flex-col gap-1">
                  <label for="edit-footer" class="text-xs font-medium text-gray-600">Подвал</label>
                  <input
                    id="edit-footer"
                    :value="editFooter"
                    type="text"
                    class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    @input="onEditFooter"
                  />
                </div>
              </template>
            </div>
          </aside>
        </div>
      </template>
    </template>

    <div v-else class="text-gray-500">
      Загрузка…
    </div>
  </div>
</template>

<script setup lang="ts">
import { DEFAULT_DESIGN } from "~/types/design";
import type {
  CarouselWithDesignResponse,
  DesignResponse,
  DesignSnapshot,
  DesignUpdate,
} from "~/types/design";
import type { SlideResponse, SlideUpdate } from "~/types/slide";
import type { CarouselResponse } from "~/types/carousel";
import type {
  GenerationResponse,
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
const editorSlides = ref<SlideResponse[]>([]);
const editorSlidesLoading = ref(false);
const currentSlideIndex = ref(0);
const editorDesign = ref<DesignSnapshot>({ ...DEFAULT_DESIGN });
const editorDesignThumb = computed(() => ({ ...editorDesign.value, padding: 8 }));

const DEBOUNCE_MS = 500;
const DESIGN_DEBOUNCE_MS = 800;
let debounceTimers: Record<string, ReturnType<typeof setTimeout>> = {};
let designDebounceTimer: ReturnType<typeof setTimeout> | null = null;
const pendingDesignPatch = ref<DesignUpdate>({});

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

const currentSlide = computed(() => {
  const list = editorSlides.value;
  const idx = currentSlideIndex.value;
  if (!list.length || idx < 0 || idx >= list.length) return null;
  return list[idx];
});

const editTitle = ref("");
const editBody = ref("");
const editFooter = ref("");

function syncEditFieldsFromSlide() {
  const s = currentSlide.value;
  if (s) {
    editTitle.value = s.title;
    editBody.value = s.body;
    editFooter.value = s.footer;
  } else {
    editTitle.value = "";
    editBody.value = "";
    editFooter.value = "";
  }
}

watch(currentSlide, syncEditFieldsFromSlide, { immediate: true });

function mergeDesignUpdate(prev: DesignUpdate, next: DesignUpdate): DesignUpdate {
  return {
    template: next.template ?? prev.template,
    background:
      next.background || prev.background
        ? {
            type: next.background?.type ?? prev.background?.type,
            value: next.background?.value ?? prev.background?.value,
            overlay: next.background?.overlay ?? prev.background?.overlay,
          }
        : undefined,
    layout:
      next.layout || prev.layout
        ? {
            padding: next.layout?.padding ?? prev.layout?.padding,
            alignment_h: next.layout?.alignment_h ?? prev.layout?.alignment_h,
            alignment_v: next.layout?.alignment_v ?? prev.layout?.alignment_v,
          }
        : undefined,
    header:
      next.header || prev.header
        ? {
            enabled: next.header?.enabled ?? prev.header?.enabled,
            text: next.header?.text ?? prev.header?.text,
          }
        : undefined,
    footer:
      next.footer || prev.footer
        ? {
            enabled: next.footer?.enabled ?? prev.footer?.enabled,
            text: next.footer?.text ?? prev.footer?.text,
          }
        : undefined,
  };
}

function applyDesignUpdate(snapshot: DesignSnapshot, update: DesignUpdate): DesignSnapshot {
  return {
    template: update.template ?? snapshot.template,
    background_type: update.background?.type ?? snapshot.background_type,
    background_value: update.background?.value ?? snapshot.background_value,
    overlay: update.background?.overlay ?? snapshot.overlay,
    padding: update.layout?.padding ?? snapshot.padding,
    alignment_h: update.layout?.alignment_h ?? snapshot.alignment_h,
    alignment_v: update.layout?.alignment_v ?? snapshot.alignment_v,
    header_enabled: update.header?.enabled ?? snapshot.header_enabled,
    header_text: update.header?.text ?? snapshot.header_text,
    footer_enabled: update.footer?.enabled ?? snapshot.footer_enabled,
    footer_text: update.footer?.text ?? snapshot.footer_text,
  };
}

function designSnapshotToUpdate(s: DesignSnapshot): DesignUpdate {
  return {
    template: s.template,
    background: { type: s.background_type, value: s.background_value, overlay: s.overlay },
    layout: { padding: s.padding, alignment_h: s.alignment_h, alignment_v: s.alignment_v },
    header: { enabled: s.header_enabled, text: s.header_text },
    footer: { enabled: s.footer_enabled, text: s.footer_text },
  };
}

async function fetchDesign() {
  try {
    const res = await request<DesignResponse>(
      `/api/v1/carousels/${id.value}/design`
    );
    editorDesign.value = { ...res.design };
  } catch {
    // useApi shows toast; keep current editorDesign to avoid overwriting with defaults
  }
}

async function patchDesign(payload: DesignUpdate, applyToAll: boolean) {
  try {
    const url = `/api/v1/carousels/${id.value}/design${applyToAll ? "?apply_to_all=true" : ""}`;
    const data = await request<CarouselWithDesignResponse>(url, {
      method: "PATCH",
      body: payload,
    });
    // Only sync server response when no pending local changes to avoid overwriting in-flight edits
    const hasPending =
      designDebounceTimer !== null ||
      Object.keys(pendingDesignPatch.value).length > 0;
    if (!hasPending) {
      editorDesign.value = { ...data.design };
    }
  } catch {
    // useApi shows toast
  }
}

function onDesignUpdate(partial: DesignUpdate) {
  editorDesign.value = applyDesignUpdate(editorDesign.value, partial);
  pendingDesignPatch.value = mergeDesignUpdate(pendingDesignPatch.value, partial);
  if (designDebounceTimer) clearTimeout(designDebounceTimer);
  designDebounceTimer = setTimeout(() => {
    const payload = { ...pendingDesignPatch.value };
    pendingDesignPatch.value = {};
    designDebounceTimer = null;
    patchDesign(payload, false);
  }, DESIGN_DEBOUNCE_MS);
}

function onDesignApplyToAll() {
  if (designDebounceTimer) {
    clearTimeout(designDebounceTimer);
    designDebounceTimer = null;
  }
  const payload = designSnapshotToUpdate(editorDesign.value);
  pendingDesignPatch.value = {};
  patchDesign(payload, true);
}

async function patchSlide(payload: SlideUpdate) {
  const s = currentSlide.value;
  if (!s) return;
  try {
    const updated = await request<SlideResponse>(
      `/api/v1/carousels/${id.value}/slides/${s.id}`,
      { method: "PATCH", body: payload }
    );
    const list = [...editorSlides.value];
    const idx = editorSlides.value.findIndex((x) => x.id === s.id);
    if (idx !== -1) list[idx] = updated;
    editorSlides.value = list;
  } catch {
    // useApi shows toast
  }
}

function schedulePatch(field: "title" | "body" | "footer", getPayload: () => SlideUpdate) {
  const key = `${currentSlide.value?.id ?? ""}-${field}`;
  if (debounceTimers[key]) clearTimeout(debounceTimers[key]);
  debounceTimers[key] = setTimeout(() => {
    patchSlide(getPayload());
    delete debounceTimers[key];
  }, DEBOUNCE_MS);
}

function onEditTitle(e: Event) {
  const v = (e.target as HTMLTextAreaElement).value;
  editTitle.value = v;
  schedulePatch("title", () => ({ title: v }));
}

function onEditBody(e: Event) {
  const v = (e.target as HTMLTextAreaElement).value;
  editBody.value = v;
  schedulePatch("body", () => ({ body: v }));
}

function onEditFooter(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  editFooter.value = v;
  schedulePatch("footer", () => ({ footer: v }));
}

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
    if (gen.status === "done") {
      stopPolling();
      await fetchCarousel();
      await ensureEditorSlides();
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
  editorSlidesLoading.value = true;
  try {
    const slides = await request<SlideResponse[]>(
      `/api/v1/carousels/${id.value}/slides`
    );
    editorSlides.value = slides;
    if (currentSlideIndex.value >= slides.length) currentSlideIndex.value = Math.max(0, slides.length - 1);
  } catch {
    editorSlides.value = [];
  } finally {
    editorSlidesLoading.value = false;
  }
}

watch(
  () => viewMode.value,
  async (mode) => {
    if (mode === "editor") {
      await Promise.all([ensureEditorSlides(), fetchDesign()]);
    }
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
  Object.values(debounceTimers).forEach(clearTimeout);
  if (designDebounceTimer) clearTimeout(designDebounceTimer);
});
</script>
