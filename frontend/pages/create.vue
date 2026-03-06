<template>
  <div>
    <div role="status" aria-live="polite" class="sr-only">
      Шаг {{ step + 1 }} из 3
    </div>
      <nav aria-label="Хлебные крошки" class="mb-6 flex items-center gap-2 text-sm text-gray-700">
      <NuxtLink
        to="/"
        class="transition-colors hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
      >
        Карусели
      </NuxtLink>
      <span aria-hidden="true">/</span>
      <span class="text-gray-900">Новая карусель</span>
    </nav>

    <template v-if="step === 0">
      <h1 class="mb-2 font-sans text-2xl font-bold text-gray-900">
        Выберите источник
      </h1>
      <p class="mb-8 text-gray-700">
        Откуда взять контент для карусели?
      </p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <button
          type="button"
          :aria-pressed="sourceType === 'text'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          @click="chooseSource('text')"
        >
          <span class="mb-2 text-2xl" aria-hidden="true">📝</span>
          <span class="font-semibold text-gray-900">Из текста</span>
          <span class="mt-1 text-sm text-gray-500">Вставьте или введите текст</span>
        </button>
        <button
          type="button"
          :aria-pressed="sourceType === 'video'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          @click="chooseSource('video')"
        >
          <span class="mb-2 text-2xl" aria-hidden="true">🎬</span>
          <span class="font-semibold text-gray-900">Из видео</span>
          <span class="mt-1 text-sm text-gray-500">Ссылка или загрузка файла</span>
        </button>
        <button
          type="button"
          :aria-pressed="sourceType === 'links'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          @click="chooseSource('links')"
        >
          <span class="mb-2 text-2xl" aria-hidden="true">🔗</span>
          <span class="font-semibold text-gray-900">Из ссылок</span>
          <span class="mt-1 text-sm text-gray-500">Список URL для разбора</span>
        </button>
      </div>
    </template>

    <template v-else-if="step === 1">
      <h1 ref="step1Heading" tabindex="-1" class="mb-2 font-sans text-2xl font-bold text-gray-900">
        Исходные данные
      </h1>
      <p class="mb-6 text-gray-700">
        {{ sourceType === 'text' ? 'Введите или вставьте текст' : sourceType === 'video' ? 'Укажите ссылку на видео (файл можно загрузить после создания)' : 'Введите ссылки (по одной на строку)' }}
      </p>

      <div v-if="sourceType === 'text'" class="space-y-4">
        <label for="source-text" class="block text-sm font-medium text-gray-700">Текст</label>
        <textarea
          id="source-text"
          v-model="payloadText"
          rows="10"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="Вставьте сюда текст для карусели…"
          :aria-describedby="inputError ? 'source-text-error' : undefined"
          :aria-invalid="inputError ? 'true' : undefined"
        />
        <p v-if="inputError" id="source-text-error" class="text-sm text-red-600">
          {{ inputError }}
        </p>
      </div>

      <div v-else-if="sourceType === 'video'" class="space-y-4">
        <label for="video-url" class="block text-sm font-medium text-gray-700">Ссылка на видео (необязательно)</label>
        <input
          id="video-url"
          v-model="payloadVideoUrl"
          type="url"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="https://…"
        />
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">Видеофайл</label>
          <input
            ref="videoFileInput"
            type="file"
            accept=".mp4,.mov,.avi,video/mp4,video/quicktime,video/x-msvideo"
            class="hidden"
            aria-label="Выбрать видеофайл"
            @change="onVideoFileChange"
          >
          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              @click="videoFileInput?.click()"
            >
              Загрузить файл
            </button>
            <template v-if="videoFile">
              <span class="text-sm text-gray-700">{{ videoFile.name }}</span>
              <button
                type="button"
                class="text-sm text-gray-600 underline hover:text-gray-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded"
                @click="clearVideoFile"
              >
                Удалить файл
              </button>
            </template>
          </div>
          <p class="text-sm text-gray-500">
            mp4, mov или avi, до 50 МБ. Можно указать ссылку выше или загрузить файл.
          </p>
        </div>
        <div class="space-y-2">
          <label for="video-transcript" class="block text-sm font-medium text-gray-700">Описание или расшифровка видео (для генерации слайдов)</label>
          <textarea
            id="video-transcript"
            v-model="payloadVideoTranscript"
            rows="5"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Вставьте расшифровку видео или краткое описание содержимого — по нему будут сгенерированы слайды."
          />
          <p class="text-sm text-gray-500">
            Без этого текста генерация слайдов из видео будет недоступна. Можно добавить позже в редакторе.
          </p>
        </div>
      </div>

      <div v-else-if="sourceType === 'links'" class="space-y-4">
        <label for="source-links" class="block text-sm font-medium text-gray-700">Ссылки (по одной на строку)</label>
        <textarea
          id="source-links"
          v-model="payloadLinksText"
          rows="8"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="https://example.com/page1&#10;https://example.com/page2"
          :aria-describedby="inputError ? 'source-links-error' : undefined"
          :aria-invalid="inputError ? 'true' : undefined"
        />
        <p v-if="inputError" id="source-links-error" class="text-sm text-red-600">
          {{ inputError }}
        </p>
      </div>

      <div class="mt-8 flex flex-wrap gap-3">
        <button
          type="button"
          class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          aria-label="Вернуться к выбору источника"
          @click="step = 0"
        >
          Назад
        </button>
        <button
          type="button"
          class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          aria-label="Перейти к настройке формата"
          @click="goToFormat"
        >
          Далее
        </button>
      </div>
    </template>

    <template v-else-if="step === 2">
      <h1 class="mb-2 font-sans text-2xl font-bold text-gray-900">
        Настроить формат
      </h1>
      <p class="mb-6 text-gray-700">
        Количество слайдов, язык и стиль поста.
      </p>

      <form class="space-y-6" @submit.prevent="submit">
        <div>
          <label for="slides-count" class="block text-sm font-medium text-gray-700">Количество слайдов</label>
          <select
            id="slides-count"
            v-model.number="formatSlidesCount"
            class="mt-1 w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option v-for="n in 5" :key="n" :value="n + 5">
              {{ n + 5 }}
            </option>
          </select>
        </div>

        <fieldset>
          <legend class="block text-sm font-medium text-gray-700">Язык</legend>
          <div class="mt-2 flex flex-wrap gap-4">
            <label class="inline-flex cursor-pointer items-center gap-2">
              <input
                v-model="formatLanguage"
                type="radio"
                value="ru"
                class="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
              />
              <span>RU</span>
            </label>
            <label class="inline-flex cursor-pointer items-center gap-2">
              <input
                v-model="formatLanguage"
                type="radio"
                value="en"
                class="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
              />
              <span>EN</span>
            </label>
            <label class="inline-flex cursor-pointer items-center gap-2">
              <input
                v-model="formatLanguage"
                type="radio"
                value="fr"
                class="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
              />
              <span>FR</span>
            </label>
          </div>
        </fieldset>

        <div>
          <label for="style-hint" class="block text-sm font-medium text-gray-700">Пример поста</label>
          <textarea
            id="style-hint"
            v-model="formatStyleHint"
            rows="3"
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Краткий пример стиля или тона поста (необязательно)"
          />
        </div>

        <p v-if="formatError" class="text-sm text-red-600">
          {{ formatError }}
        </p>

        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            aria-label="Вернуться к исходным данным"
            @click="goBack"
          >
            Назад
          </button>
          <button
            type="submit"
            class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            :disabled="submitting"
            :aria-label="submitting ? 'Создание карусели…' : 'Создать карусель'"
          >
            {{ submitting ? 'Создание…' : 'Создать' }}
          </button>
        </div>
      </form>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { CarouselResponse, CreateCarouselPayload, SourceType } from "~/types/carousel";

const { request } = useApi();

const step = ref(0);
const sourceType = ref<SourceType | null>(null);

const payloadText = ref("");
const payloadVideoUrl = ref("");
const payloadVideoTranscript = ref("");
const payloadLinksText = ref("");
const videoFile = ref<File | null>(null);
const videoFileInput = ref<HTMLInputElement | null>(null);

const formatSlidesCount = ref(8);
const formatLanguage = ref<"ru" | "en" | "fr">("ru");
const formatStyleHint = ref("");

const inputError = ref("");
const formatError = ref("");
const submitting = ref(false);

const step1Heading = ref<HTMLHeadingElement | null>(null);

function chooseSource(type: SourceType) {
  sourceType.value = type;
  inputError.value = "";
  payloadText.value = "";
  payloadVideoUrl.value = "";
  payloadVideoTranscript.value = "";
  payloadLinksText.value = "";
  videoFile.value = null;
  step.value = 1;
  nextTick(() => step1Heading.value?.focus());
}

function onVideoFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  videoFile.value = file ?? null;
}

function clearVideoFile() {
  videoFile.value = null;
  if (videoFileInput.value) videoFileInput.value.value = "";
}

function goBack() {
  step.value = 1;
  formatError.value = "";
  nextTick(() => step1Heading.value?.focus());
}

function validateInput(): boolean {
  inputError.value = "";
  if (sourceType.value === "text") {
    const t = payloadText.value.trim();
    if (!t) {
      inputError.value = "Введите текст.";
      return false;
    }
    return true;
  }
  if (sourceType.value === "video") {
    return true;
  }
  if (sourceType.value === "links") {
    const lines = payloadLinksText.value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    if (lines.length === 0) {
      inputError.value = "Введите хотя бы одну ссылку.";
      return false;
    }
    for (const line of lines) {
      try {
        new URL(line);
      } catch {
        inputError.value = "Некоторые ссылки имеют неверный формат.";
        return false;
      }
    }
    return true;
  }
  return false;
}

function goToFormat() {
  if (!validateInput()) return;
  formatError.value = "";
  step.value = 2;
}

function validateFormat(): boolean {
  formatError.value = "";
  const count = formatSlidesCount.value;
  if (count < 6 || count > 10) {
    formatError.value = "Количество слайдов должно быть от 6 до 10.";
    return false;
  }
  return true;
}

function buildSourcePayload(): Record<string, unknown> {
  if (sourceType.value === "text") {
    return { source_text: payloadText.value.trim() };
  }
  if (sourceType.value === "video") {
    const url = payloadVideoUrl.value.trim();
    const transcript = payloadVideoTranscript.value.trim();
    const out: Record<string, unknown> = {};
    if (url) out.video_url = url;
    if (transcript) out.video_transcript = transcript;
    return out;
  }
  if (sourceType.value === "links") {
    const urls = payloadLinksText.value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    return { links: urls };
  }
  return {};
}

async function submit() {
  if (!validateFormat() || sourceType.value === null) return;
  submitting.value = true;
  formatError.value = "";

  const payload: CreateCarouselPayload = {
    title: "",
    source_type: sourceType.value,
    source_payload: buildSourcePayload(),
    format: {
      slides_count: formatSlidesCount.value,
      language: formatLanguage.value,
      style_hint: formatStyleHint.value.trim() || undefined,
    },
  };

  try {
    const data = await request<CarouselResponse>("/api/v1/carousels", {
      method: "POST",
      body: payload,
    });
    if (sourceType.value === "video" && videoFile.value) {
      const form = new FormData();
      form.append("file", videoFile.value);
      await request<CarouselResponse>(`/api/v1/carousels/${data.id}/video`, {
        method: "POST",
        body: form,
      });
    }
    await navigateTo(`/carousels/${data.id}`);
  } catch {
    // handled by useApi toast
  } finally {
    submitting.value = false;
  }
}
</script>
