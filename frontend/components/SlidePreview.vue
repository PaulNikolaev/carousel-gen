<template>
  <div
    class="slide-preview flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
    :class="templateClass"
    :style="containerStyle"
  >
    <div
      v-if="design.background_type === 'image' && design.overlay > 0"
      class="slide-preview__overlay"
      :style="{ background: `rgba(0,0,0,${design.overlay})` }"
      aria-hidden="true"
    />
    <header
      v-if="design.header_enabled"
      class="slide-preview__header flex shrink-0 items-center justify-between py-2 text-[10px] opacity-90"
    >
      <span class="slide-preview__header-text">{{ design.header_text || " " }}</span>
      <span class="slide-preview__counter">{{ slideIndex }} / {{ totalSlides }}</span>
    </header>
    <div
      class="slide-preview__content flex flex-1 flex-col gap-4 py-3"
      :style="contentAlignStyle"
    >
      <h2
        v-if="slide.title"
        class="slide-preview__title text-xl font-medium leading-tight"
      >
        {{ slide.title }}
      </h2>
      <p
        v-if="slide.body"
        class="slide-preview__body text-[11px] leading-relaxed"
      >
        {{ slide.body }}
      </p>
    </div>
    <footer
      v-if="design.footer_enabled"
      class="slide-preview__footer flex shrink-0 items-center justify-between py-2 text-[10px] opacity-90"
    >
      <span class="slide-preview__footer-text">{{ design.footer_text || slide.footer || " " }}</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import type { DesignSnapshot } from "~/types/design";

interface SlideContent {
  title: string;
  body: string;
  footer: string;
}

const props = withDefaults(
  defineProps<{
    slide: SlideContent;
    design: DesignSnapshot;
    slideIndex?: number;
    totalSlides?: number;
  }>(),
  {
    slideIndex: 1,
    totalSlides: 1,
  }
);

const templateClass = computed(() => `slide-preview--${props.design.template}`);

const containerStyle = computed(() => {
  const d = props.design;
  const pad = d.padding;
  const bg =
    d.background_type === "image" && d.background_value
      ? `url("${d.background_value.replace(/\\/g, "\\\\").replace(/"/g, "%22")}")`
      : d.background_value || "#FFFFFF";
  return {
    aspectRatio: "4 / 5",
    padding: `${pad}px`,
    background: bg,
    backgroundSize: "cover",
    backgroundPosition: "center",
    position: "relative",
  };
});

const contentAlignStyle = computed(() => {
  const d = props.design;
  const justify =
    d.alignment_v === "top"
      ? "flex-start"
      : d.alignment_v === "bottom"
        ? "flex-end"
        : "center";
  const align =
    d.alignment_h === "left"
      ? "flex-start"
      : d.alignment_h === "right"
        ? "flex-end"
        : "center";
  const textAlign =
    d.alignment_h === "left"
      ? "left"
      : d.alignment_h === "right"
        ? "right"
        : "center";
  return {
    justifyContent: justify,
    alignItems: align,
    textAlign,
  };
});
</script>

<style scoped>
.slide-preview {
  letter-spacing: 0.01em;
  position: relative;
}

.slide-preview__overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.slide-preview__header,
.slide-preview__content,
.slide-preview__footer {
  position: relative;
  z-index: 1;
}

.slide-preview--classic {
  --tpl-heading-font: "Inter", system-ui, sans-serif;
  --tpl-heading-weight: 500;
  --tpl-body-font: "Inter", system-ui, sans-serif;
  --tpl-accent: #3e28c8;
  --tpl-text: #232323;
}

.slide-preview--bold {
  --tpl-heading-font: "Arsenal", "Inter", system-ui, sans-serif;
  --tpl-heading-weight: 700;
  --tpl-body-font: "Inter", system-ui, sans-serif;
  --tpl-accent: #bd2d36;
  --tpl-text: #0f0f0f;
}

.slide-preview--minimal {
  --tpl-heading-font: "Montserrat", "Inter", system-ui, sans-serif;
  --tpl-heading-weight: 600;
  --tpl-body-font: "Inter", system-ui, sans-serif;
  --tpl-accent: #8664f9;
  --tpl-text: #232323;
}

.slide-preview__title {
  font-family: var(--tpl-heading-font);
  font-weight: var(--tpl-heading-weight);
  color: var(--tpl-accent);
  letter-spacing: -0.01em;
}

.slide-preview__body {
  font-family: var(--tpl-body-font);
  color: var(--tpl-text);
  letter-spacing: 0.01em;
}

.slide-preview__header,
.slide-preview__footer {
  color: var(--tpl-text);
  font-family: var(--tpl-body-font);
}
</style>
