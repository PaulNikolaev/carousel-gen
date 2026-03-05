<template>
  <div>
    <div role="status" aria-live="polite" class="sr-only">
      Шаг {{ step + 1 }} из 3
    </div>
    <nav aria-label="Хлебные крошки" class="mb-6 flex items-center gap-2 text-sm text-gray-600">
      <NuxtLink to="/" class="transition-colors hover:text-primary">
        Карусели
      </NuxtLink>
      <span aria-hidden="true">/</span>
      <span class="text-gray-900">Новая карусель</span>
    </nav>

    <template v-if="step === 0">
      <h1 class="mb-2 font-sans text-2xl font-bold text-gray-900">
        Выберите источник
      </h1>
      <p class="mb-8 text-gray-600">
        Откуда взять контент для карусели?
      </p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <button
          type="button"
          :aria-pressed="sourceType === 'text'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          @click="chooseSource('text')"
        >
          <span class="mb-2 text-2xl" aria-hidden="true">📝</span>
          <span class="font-semibold text-gray-900">Из текста</span>
          <span class="mt-1 text-sm text-gray-500">Вставьте или введите текст</span>
        </button>
        <button
          type="button"
          :aria-pressed="sourceType === 'video'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          @click="chooseSource('video')"
        >
          <span class="mb-2 text-2xl" aria-hidden="true">🎬</span>
          <span class="font-semibold text-gray-900">Из видео</span>
          <span class="mt-1 text-sm text-gray-500">Ссылка или загрузка файла</span>
        </button>
        <button
          type="button"
          :aria-pressed="sourceType === 'links'"
          class="flex flex-col rounded-xl border-2 border-gray-200 bg-white p-6 text-left shadow-sm transition-all hover:border-primary hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
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
      <p class="mb-6 text-gray-600">
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
        />
        <p v-if="inputError" class="text-sm text-red-600">
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
        <p class="text-sm text-gray-500">
          Файл можно загрузить после создания карусели в редакторе.
        </p>
      </div>

      <div v-else-if="sourceType === 'links'" class="space-y-4">
        <label for="source-links" class="block text-sm font-medium text-gray-700">Ссылки (по одной на строку)</label>
        <textarea
          id="source-links"
          v-model="payloadLinksText"
          rows="8"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="https://example.com/page1&#10;https://example.com/page2"
        />
        <p v-if="inputError" class="text-sm text-red-600">
          {{ inputError }}
        </p>
      </div>

      <div class="mt-8 flex flex-wrap gap-3">
        <button
          type="button"
          class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
          @click="step = 0"
        >
          Назад
        </button>
        <button
          type="button"
          class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90"
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
      <p class="mb-6 text-gray-600">
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

        <div>
          <label class="block text-sm font-medium text-gray-700">Язык</label>
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
        </div>

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
            class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
            @click="goBack"
          >
            Назад
          </button>
          <button
            type="submit"
            class="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 disabled:opacity-50"
            :disabled="submitting"
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

definePageMeta({ layout: "default" });

const { request } = useApi();

const step = ref(0);
const sourceType = ref<SourceType | null>(null);

const payloadText = ref("");
const payloadVideoUrl = ref("");
const payloadLinksText = ref("");

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
  payloadLinksText.value = "";
  step.value = 1;
  nextTick(() => step1Heading.value?.focus());
}

function goBack() {
  step.value = 1;
  formatError.value = "";
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
    return url ? { video_url: url } : {};
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
    await navigateTo(`/carousels/${data.id}`);
  } catch {
    // handled by useApi toast
  } finally {
    submitting.value = false;
  }
}
</script>
