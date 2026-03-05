<template>
  <div class="font-sans tracking-[-0.025em]" style="font-size: 13.5px;">
    <nav aria-label="Хлебные крошки" class="mb-4 flex items-center gap-2 text-gray-700">
      <NuxtLink
        to="/"
        class="transition-colors hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
      >
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
          class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-white shadow-sm transition-colors hover:bg-primary/90 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          :disabled="starting"
          aria-label="Запустить генерацию слайдов"
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
        <div role="status" aria-live="polite" class="flex items-center gap-3">
          <span
            class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"
            aria-hidden="true"
          />
          <span class="text-gray-700">{{ progressStatusText }}</span>
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
          class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-white shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          aria-label="Повторить генерацию"
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
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              :disabled="!canRegenerate"
              aria-label="Сгенерировать слайды заново"
              @click="startGeneration"
            >
              Сгенерировать заново
            </button>
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-white shadow-sm transition-colors hover:bg-primary/90 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              :disabled="!canExport"
              aria-label="Экспорт карусели в ZIP"
              @click="startExport"
            >
              Экспорт
            </button>
            <NuxtLink
              to="/"
              class="text-accent font-medium transition-colors hover:text-accent/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
              aria-label="Готово, вернуться к списку каруселей"
            >
              Готово
            </NuxtLink>
            <button
              ref="settingsButtonRef"
              type="button"
              class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 md:hidden"
              aria-label="Открыть настройки дизайна"
              @click="designSheetOpen = true"
            >
              Настройки
            </button>
          </div>
        </div>
        <!-- Export progress -->
        <div
          v-if="exportStatus === 'pending' || exportStatus === 'running'"
          class="mb-4 flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
        >
          <span
            class="inline-block h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-primary border-t-transparent"
            aria-hidden="true"
          />
          <span class="text-gray-700">Экспорт…</span>
        </div>
        <div
          v-else-if="exportStatus === 'done' && exportDownloadUrl"
          class="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3"
        >
          <a
            :href="exportDownloadUrl"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Скачать ZIP (откроется в новой вкладке)"
            class="text-primary font-medium underline transition-colors hover:text-primary/90"
          >
            Скачать ZIP
          </a>
        </div>
        <div
          v-else-if="exportStatus === 'done' && !exportDownloadUrl"
          class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700"
        >
          Экспорт завершён, но ссылка для скачивания недоступна.
        </div>
        <div
          v-else-if="exportStatus === 'failed'"
          class="mb-4 flex flex-wrap items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700"
        >
          <span>{{ exportError || "Экспорт не удался." }}</span>
          <button
            type="button"
            class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-white transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            aria-label="Повторить экспорт"
            @click="startExport"
          >
            Повторить
          </button>
        </div>
        <!-- История генераций -->
        <details class="mb-4 rounded-lg border border-gray-200 bg-gray-50/50">
          <summary class="cursor-pointer px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset rounded-lg">
            История генераций
          </summary>
          <div class="border-t border-gray-200 px-4 py-3">
            <p v-if="generationsLoading" class="text-gray-500 text-sm">
              Загрузка…
            </p>
            <p v-else-if="!generationsList.length" class="text-gray-500 text-sm">
              Нет записей.
            </p>
            <div v-else class="flex flex-col gap-2">
              <button
                v-for="gen in generationsList"
                :key="gen.id"
                type="button"
                class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-left text-sm transition-colors hover:border-gray-300 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                @click="openGenerationResult(gen.id)"
              >
                <span class="text-gray-700">{{ formatGenerationDate(gen.created_at) }}</span>
                <span
                  class="rounded px-2 py-0.5 text-xs font-medium"
                  :class="generationStatusBadgeClass(gen.status)"
                >
                  {{ generationStatusLabel(gen.status) }}
                </span>
                <span v-if="gen.tokens_used != null" class="text-gray-500 text-xs">
                  {{ gen.tokens_used }} токенов
                </span>
              </button>
            </div>
          </div>
        </details>
        <!-- Модальное окно результата генерации -->
        <Teleport to="body">
          <div
            v-if="generationResultModalOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            role="dialog"
            aria-modal="true"
            aria-label="Результат генерации"
            @click.self="generationResultModalOpen = false"
          >
            <div
              ref="generationResultDialogRef"
              tabindex="-1"
              class="max-h-[90vh] w-full max-w-lg overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl"
              @click.stop
              @keydown.esc="generationResultModalOpen = false"
            >
              <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                <h3 class="text-sm font-semibold text-gray-900">
                  Результат генерации
                </h3>
                <button
                  type="button"
                  class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  aria-label="Закрыть"
                  @click="generationResultModalOpen = false"
                >
                  ✕
                </button>
              </div>
              <div class="max-h-[70vh] overflow-y-auto p-4">
                <p v-if="generationResultLoading" class="text-gray-500 text-sm">
                  Загрузка…
                </p>
                <p v-else-if="generationResultError" class="text-red-600 text-sm">
                  Не удалось загрузить результат генерации.
                </p>
                <template v-else-if="selectedGenerationResult">
                  <div
                    v-if="!selectedGenerationResult.result?.length"
                    class="text-gray-500 text-sm"
                  >
                    Нет слайдов (статус: {{ selectedGenerationResult.status }}).
                  </div>
                  <ul v-else class="flex flex-col gap-3">
                    <li
                      v-for="(slide, idx) in selectedGenerationResult.result"
                      :key="idx"
                      class="rounded border border-gray-200 p-3 text-sm"
                    >
                      <div class="font-medium text-gray-900">{{ slide.title || '—' }}</div>
                      <div class="mt-1 text-gray-600">{{ slide.body || '—' }}</div>
                      <div v-if="slide.footer" class="mt-1 text-gray-500 text-xs">{{ slide.footer }}</div>
                    </li>
                  </ul>
                </template>
              </div>
            </div>
          </div>
        </Teleport>
        <p v-if="editorSlidesLoading" role="status" class="text-gray-500">
          Загрузка слайдов…
        </p>
        <template v-else>
          <!-- Desktop: grid thumbnails | preview | aside -->
          <div
            class="hidden gap-4 md:grid"
            style="grid-template-columns: minmax(0, 120px) minmax(0, 1fr) minmax(0, 280px);"
          >
            <div class="flex flex-col gap-2 overflow-y-auto">
              <button
                v-for="(s, idx) in editorSlides"
                :key="s.id"
                type="button"
                class="slide-thumb flex shrink-0 overflow-hidden rounded border-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
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
                    <label for="edit-title" class="text-xs font-medium text-gray-700">Заголовок</label>
                    <textarea
                      id="edit-title"
                      :value="editTitle"
                      rows="2"
                      class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      @input="onEditTitle"
                    />
                  </div>
                  <div class="flex flex-col gap-1">
                    <label for="edit-body" class="text-xs font-medium text-gray-700">Текст</label>
                    <textarea
                      id="edit-body"
                      :value="editBody"
                      rows="4"
                      class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      @input="onEditBody"
                    />
                  </div>
                  <div class="flex flex-col gap-1">
                    <label for="edit-footer" class="text-xs font-medium text-gray-700">Подвал</label>
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

          <!-- Mobile: preview + horizontal thumbnails strip -->
          <div class="flex flex-col gap-4 md:hidden">
            <div class="flex min-h-0 justify-center">
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
            <div
              class="flex gap-2 overflow-x-auto pb-2"
              style="min-height: 90px;"
            >
              <button
                v-for="(s, idx) in editorSlides"
                :key="s.id"
                type="button"
                class="slide-thumb-mobile flex h-[90px] shrink-0 overflow-hidden rounded border-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                :class="currentSlideIndex === idx ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'"
                :aria-label="`Слайд ${s.order}`"
                :aria-pressed="currentSlideIndex === idx"
                style="aspect-ratio: 4/5;"
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
          </div>

          <!-- Bottom-sheet: design panel + slide fields (mobile) -->
          <Teleport to="body">
            <Transition name="sheet-backdrop">
              <div
                v-show="designSheetOpen"
                class="fixed inset-0 z-40 bg-black/40 md:hidden"
                aria-hidden="true"
                @click="designSheetOpen = false"
              />
            </Transition>
            <Transition name="sheet-slide">
              <div
                ref="sheetDialogRef"
                v-show="designSheetOpen"
                class="fixed bottom-0 left-0 right-0 z-50 max-h-[80vh] overflow-y-auto rounded-t-xl border border-gray-200 border-b-0 bg-white shadow-xl md:hidden"
                role="dialog"
                aria-modal="true"
                aria-label="Настройки дизайна и текст слайда"
                @keydown.esc="designSheetOpen = false"
              >
                <div class="sticky top-0 flex justify-end border-b border-gray-200 bg-white p-2">
                  <button
                    ref="sheetCloseButtonRef"
                    type="button"
                    class="rounded-md p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    aria-label="Закрыть настройки"
                    @click="designSheetOpen = false"
                  >
                    <span aria-hidden="true">✕</span>
                  </button>
                </div>
                <div class="flex flex-col gap-4 p-4">
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
                        <label for="edit-title-mobile" class="text-xs font-medium text-gray-700">Заголовок</label>
                        <textarea
                          id="edit-title-mobile"
                          :value="editTitle"
                          rows="2"
                          class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                          @input="onEditTitle"
                        />
                      </div>
                      <div class="flex flex-col gap-1">
                        <label for="edit-body-mobile" class="text-xs font-medium text-gray-700">Текст</label>
                        <textarea
                          id="edit-body-mobile"
                          :value="editBody"
                          rows="4"
                          class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                          @input="onEditBody"
                        />
                      </div>
                      <div class="flex flex-col gap-1">
                        <label for="edit-footer-mobile" class="text-xs font-medium text-gray-700">Подвал</label>
                        <input
                          id="edit-footer-mobile"
                          :value="editFooter"
                          type="text"
                          class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                          @input="onEditFooter"
                        />
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </Transition>
          </Teleport>
        </template>
      </template>
    </template>

    <div v-else role="status" class="text-gray-500">
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
  CarouselGenerationsResponse,
  GenerationListItem,
  GenerationResponse,
  StartGenerationResponse,
} from "~/types/generation";
import type { ExportResponse, StartExportResponse } from "~/types/export";

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

let generationEventSource: EventSource | null = null;
let exportEventSource: EventSource | null = null;

const exportId = ref<string | null>(null);
const exportStatus = ref<ExportResponse["status"] | null>(null);
const exportDownloadUrl = ref<string | null>(null);
const exportError = ref<string | null>(null);

const designSheetOpen = ref(false);
const settingsButtonRef = ref<HTMLButtonElement | null>(null);
const sheetCloseButtonRef = ref<HTMLButtonElement | null>(null);
const sheetDialogRef = ref<HTMLElement | null>(null);

const generationsList = ref<GenerationListItem[]>([]);
const generationsLoading = ref(false);
const generationResultModalOpen = ref(false);
const selectedGenerationResult = ref<GenerationResponse | null>(null);
const generationResultLoading = ref(false);
const generationResultError = ref(false);
const generationResultDialogRef = ref<HTMLElement | null>(null);

function handleSheetKeydown(e: KeyboardEvent) {
  if (!sheetDialogRef.value) return;
  const focusable = Array.from(
    sheetDialogRef.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
  ).filter((el) => !el.hasAttribute('disabled'));
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.key === 'Tab') {
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }
}

watch(generationResultModalOpen, (open) => {
  if (open) {
    nextTick(() => generationResultDialogRef.value?.focus());
  }
});

watch(designSheetOpen, (open) => {
  if (open) {
    nextTick(() => {
      sheetCloseButtonRef.value?.focus();
      sheetDialogRef.value?.addEventListener('keydown', handleSheetKeydown);
    });
  } else {
    sheetDialogRef.value?.removeEventListener('keydown', handleSheetKeydown);
    nextTick(() => settingsButtonRef.value?.focus());
  }
});

const canExport = computed(() => {
  if (carousel.value?.status !== "ready") return false;
  if (exportStatus.value === "pending" || exportStatus.value === "running")
    return false;
  return true;
});

const canRegenerate = computed(() => {
  const status = carousel.value?.status;
  if (status !== "ready" && status !== "failed") return false;
  if (starting.value) return false;
  return true;
});

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
  closeGenerationSSE();
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
    startGenerationSSE();
  } catch {
    // useApi shows toast
  } finally {
    starting.value = false;
  }
}

function closeGenerationSSE() {
  if (generationEventSource) {
    generationEventSource.close();
    generationEventSource = null;
  }
}

function startGenerationSSE() {
  const genId = activeGenerationId.value;
  if (!genId) return;
  closeGenerationSSE();
  const config = useRuntimeConfig();
  const baseUrl = (
    (config.public.apiBaseUrl as string) || "http://localhost:8000"
  ).replace(/\/$/, "");
  const apiKey = (config.public.apiKey as string) || "";
  let streamUrl = `${baseUrl}/api/v1/generations/${genId}/stream`;
  // EventSource does not support custom headers; send api_key as query param instead.
  if (apiKey) {
    streamUrl += `${streamUrl.includes("?") ? "&" : "?"}api_key=${encodeURIComponent(apiKey)}`;
  }
  const es = new EventSource(streamUrl);
  generationEventSource = es;

  es.onmessage = async (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as GenerationResponse;
      generation.value = data;
      if (data.tokens_estimate != null) tokensEstimate.value = data.tokens_estimate;
      if (data.status === "done") {
        closeGenerationSSE();
        await fetchCarousel();
        await ensureEditorSlides();
      } else if (data.status === "failed") {
        closeGenerationSSE();
        await fetchCarousel();
      }
    } catch {
      closeGenerationSSE();
    }
  };

  es.onerror = () => {
    closeGenerationSSE();
    startCarouselPolling();
    void fetchCarousel();
  };
}

function closeExportSSE() {
  if (exportEventSource) {
    exportEventSource.close();
    exportEventSource = null;
  }
}

function clearExportState() {
  exportId.value = null;
  exportStatus.value = null;
  exportDownloadUrl.value = null;
  exportError.value = null;
  closeExportSSE();
}

function startExportSSE() {
  const expId = exportId.value;
  if (!expId) return;
  closeExportSSE();
  const config = useRuntimeConfig();
  const baseUrl = (
    (config.public.apiBaseUrl as string) || "http://localhost:8000"
  ).replace(/\/$/, "");
  const apiKey = (config.public.apiKey as string) || "";
  let streamUrl = `${baseUrl}/api/v1/exports/${expId}/stream`;
  // EventSource does not support custom headers; send api_key as query param instead.
  if (apiKey) {
    streamUrl += `${streamUrl.includes("?") ? "&" : "?"}api_key=${encodeURIComponent(apiKey)}`;
  }
  const es = new EventSource(streamUrl);
  exportEventSource = es;

  es.onmessage = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as ExportResponse;
      exportStatus.value = data.status;
      exportDownloadUrl.value = data.download_url ?? null;
      exportError.value = data.error_message ?? null;
      if (data.status === "done" || data.status === "failed") {
        closeExportSSE();
      }
    } catch {
      closeExportSSE();
    }
  };

  es.onerror = () => {
    exportStatus.value = "failed";
    closeExportSSE();
  };
}

async function startExport() {
  if (!canExport.value) return;
  clearExportState();
  exportStatus.value = "pending";
  try {
    const data = await request<StartExportResponse>("/api/v1/exports", {
      method: "POST",
      body: { carousel_id: id.value },
    });
    exportId.value = data.export_id;
    startExportSSE();
  } catch {
    exportStatus.value = null;
    // useApi shows toast
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

async function fetchGenerations() {
  if (!id.value) return;
  generationsLoading.value = true;
  try {
    const data = await request<CarouselGenerationsResponse>(
      `/api/v1/carousels/${id.value}/generations`
    );
    generationsList.value = data.items;
  } catch {
    generationsList.value = [];
  } finally {
    generationsLoading.value = false;
  }
}

function formatGenerationDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function generationStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    queued: "В очереди",
    running: "Выполняется",
    done: "Готово",
    failed: "Ошибка",
  };
  return labels[status] ?? status;
}

function generationStatusBadgeClass(status: string): string {
  if (status === "done") return "bg-green-100 text-green-800";
  if (status === "failed") return "bg-red-100 text-red-800";
  if (status === "running" || status === "queued") return "bg-gray-100 text-gray-700";
  return "bg-gray-100 text-gray-700";
}

async function openGenerationResult(genId: string) {
  generationResultModalOpen.value = true;
  selectedGenerationResult.value = null;
  generationResultLoading.value = true;
  generationResultError.value = false;
  try {
    const data = await request<GenerationResponse>(`/api/v1/generations/${genId}`);
    selectedGenerationResult.value = data;
  } catch {
    selectedGenerationResult.value = null;
    generationResultError.value = true;
  } finally {
    generationResultLoading.value = false;
  }
}

watch(
  () => viewMode.value,
  async (mode) => {
    if (mode === "editor") {
      await Promise.all([ensureEditorSlides(), fetchDesign(), fetchGenerations()]);
    }
  },
  { immediate: true }
);

watch(
  () => carousel.value?.status,
  (status) => {
    if (status === "generating" && !generationEventSource) {
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
  sheetDialogRef.value?.removeEventListener('keydown', handleSheetKeydown);
  closeGenerationSSE();
  stopCarouselPolling();
  clearExportState();
  Object.values(debounceTimers).forEach(clearTimeout);
  if (designDebounceTimer) clearTimeout(designDebounceTimer);
});
</script>

<style scoped>
.sheet-backdrop-enter-active,
.sheet-backdrop-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-backdrop-enter-from,
.sheet-backdrop-leave-to {
  opacity: 0;
}
.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: transform 0.25s ease;
}
.sheet-slide-enter-from,
.sheet-slide-leave-to {
  transform: translateY(100%);
}
</style>
