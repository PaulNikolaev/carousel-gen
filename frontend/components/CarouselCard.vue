<template>
  <article
    class="flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md"
    :aria-labelledby="titleId"
  >
    <div class="aspect-[4/5] w-full shrink-0 bg-gray-100">
      <img
        v-if="carousel.preview_url && !previewError"
        :src="carousel.preview_url"
        :alt="carousel.title"
        class="h-full w-full object-cover"
        loading="lazy"
        @error="previewError = true"
      >
      <div
        v-else
        class="flex h-full w-full items-center justify-center text-gray-400"
        aria-hidden="true"
      >
        <span class="text-4xl">📷</span>
      </div>
    </div>
    <div class="flex flex-1 flex-col p-6">
      <h2 :id="titleId" class="line-clamp-2 text-lg font-semibold text-gray-900">
        {{ carousel.title || 'Без названия' }}
      </h2>
      <p class="mt-1 text-sm text-gray-700">
        {{ formattedDate }}
      </p>
      <div class="mt-2 flex flex-wrap items-center gap-2">
        <span :class="statusBadgeClass">
          {{ statusLabel }}
        </span>
        <span class="text-xs text-gray-700">
          {{ languageLabel }} · {{ slidesLabel }}
        </span>
      </div>
      <div class="mt-4 flex flex-1 items-end">
        <NuxtLink
          :to="editorPath"
          class="inline-flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          :aria-label="`${cardButtonLabel}: ${carousel.title || 'Без названия'}`"
        >
          {{ cardButtonLabel }}
        </NuxtLink>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { CarouselResponse, CarouselStatus } from "~/types/carousel";

const props = defineProps<{
  carousel: CarouselResponse;
}>();

const titleId = computed(() => `carousel-title-${props.carousel.id}`);
const previewError = ref(false);

watch(() => props.carousel.preview_url, () => {
  previewError.value = false;
});

const formattedDate = computed(() => {
  const raw = props.carousel.created_at;
  if (!raw) return "—";
  try {
    const d = new Date(raw);
    return new Intl.DateTimeFormat("ru-RU", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(d);
  } catch {
    return "—";
  }
});

const statusLabels: Record<CarouselStatus, string> = {
  draft: "Черновик",
  generating: "Генерация",
  ready: "Готово",
  failed: "Ошибка",
};

const statusLabel = computed(
  () => statusLabels[props.carousel.status] ?? props.carousel.status
);

const statusBadgeClass = computed(() => {
  const status = props.carousel.status;
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ";
  switch (status) {
    case "draft":
      return base + "bg-gray-100 text-gray-800";
    case "generating":
      return base + "bg-amber-100 text-amber-800";
    case "ready":
      return base + "bg-green-100 text-green-800";
    case "failed":
      return base + "bg-red-100 text-red-800";
    default:
      return base + "bg-gray-100 text-gray-600";
  }
});

const languageLabels: Record<string, string> = {
  ru: "RU",
  en: "EN",
  fr: "FR",
};

const languageLabel = computed(
  () => languageLabels[props.carousel.language] ?? props.carousel.language.toUpperCase()
);

const slidesLabel = computed(() => {
  const n = props.carousel.slides_count;
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 19) return `${n} слайдов`;
  if (mod10 === 1) return `${n} слайд`;
  if (mod10 >= 2 && mod10 <= 4) return `${n} слайда`;
  return `${n} слайдов`;
});

const editorPath = computed(() => `/carousels/${props.carousel.id}`);

const cardButtonLabel = computed(() => {
  if (props.carousel.status === "draft" || props.carousel.status === "generating") {
    return "Продолжить в редакторе";
  }
  return "Открыть";
});
</script>
