<template>
  <div class="design-panel flex flex-col gap-4">
    <div role="tablist" class="flex gap-1 rounded border border-gray-200 bg-gray-100/80 p-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.id"
        class="flex-1 rounded px-2 py-1.5 text-xs font-medium transition-colors"
        :class="activeTab === tab.id ? 'bg-white text-primary shadow-sm' : 'text-gray-600 hover:text-gray-900'"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Шаблон -->
    <div
      v-show="activeTab === 'template'"
      role="tabpanel"
      class="flex flex-col gap-2"
    >
      <p class="text-xs text-gray-600">
        Пресет оформления
      </p>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="preset in templatePresets"
          :key="preset.id"
          type="button"
          class="design-panel__preset flex flex-col overflow-hidden rounded border-2 transition-colors"
          :class="design.template === preset.id ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'"
          @click="emitUpdate({ template: preset.id })"
        >
          <div
            class="h-10 w-full shrink-0"
            :style="{ background: preset.stripColor }"
          />
          <span class="p-1.5 text-center text-[11px] font-medium text-gray-700">
            {{ preset.label }}
          </span>
        </button>
      </div>
    </div>

    <!-- Фон -->
    <div
      v-show="activeTab === 'background'"
      role="tabpanel"
      class="flex flex-col gap-3"
    >
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">Тип фона</label>
        <div class="flex gap-2">
          <label class="flex cursor-pointer items-center gap-1.5">
            <input
              :checked="design.background_type === 'color'"
              type="radio"
              value="color"
              class="text-primary"
              @change="onBackgroundTypeChange('color')"
            />
            <span class="text-xs">Цвет</span>
          </label>
          <label class="flex cursor-pointer items-center gap-1.5">
            <input
              :checked="design.background_type === 'image'"
              type="radio"
              value="image"
              class="text-primary"
              @change="onBackgroundTypeChange('image')"
            />
            <span class="text-xs">Фото</span>
          </label>
        </div>
      </div>
      <div v-if="design.background_type === 'color'" class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">Цвет</label>
        <div class="flex items-center gap-2">
          <input
            :value="design.background_value"
            type="color"
            class="h-8 w-12 cursor-pointer rounded border border-gray-300"
            @input="onColorInput"
          />
          <input
            :value="design.background_value"
            type="text"
            class="flex-1 rounded border border-gray-300 px-2 py-1 text-xs"
            @input="onColorTextInput"
          />
        </div>
      </div>
      <div v-else class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">Изображение</label>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="hidden"
          @change="onFileSelect"
        />
        <button
          type="button"
          class="rounded border border-gray-300 bg-white px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
          :disabled="uploading"
          @click="fileInputRef?.click()"
        >
          {{ uploading ? "Загрузка…" : "Выбрать файл" }}
        </button>
      </div>
      <div v-show="design.background_type === 'image'" class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">
          Затемнение: {{ overlayPercent }}%
        </label>
        <input
          :value="overlayPercent"
          type="range"
          min="0"
          max="80"
          class="h-2 w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-primary"
          @input="onOverlayInput"
        />
      </div>
    </div>

    <!-- Макет -->
    <div
      v-show="activeTab === 'layout'"
      role="tabpanel"
      class="flex flex-col gap-3"
    >
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">
          Отступы: {{ design.padding }} px
        </label>
        <input
          :value="design.padding"
          type="range"
          min="8"
          max="48"
          class="h-2 w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-primary"
          @input="onPaddingInput"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">По горизонтали</label>
        <div class="flex gap-1">
          <button
            v-for="h in alignmentH"
            :key="h"
            type="button"
            class="flex-1 rounded border py-1 text-xs"
            :class="design.alignment_h === h ? 'border-primary bg-primary/10 text-primary' : 'border-gray-200 hover:border-gray-300'"
            @click="emitUpdate({ layout: { alignment_h: h } })"
          >
            {{ alignmentHLabels[h] }}
          </button>
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-600">По вертикали</label>
        <div class="flex gap-1">
          <button
            v-for="v in alignmentV"
            :key="v"
            type="button"
            class="flex-1 rounded border py-1 text-xs"
            :class="design.alignment_v === v ? 'border-primary bg-primary/10 text-primary' : 'border-gray-200 hover:border-gray-300'"
            @click="emitUpdate({ layout: { alignment_v: v } })"
          >
            {{ alignmentVLabels[v] }}
          </button>
        </div>
      </div>
    </div>

    <!-- Шапка & Подвал -->
    <div
      v-show="activeTab === 'headerfooter'"
      role="tabpanel"
      class="flex flex-col gap-4"
    >
      <div class="flex flex-col gap-2">
        <div class="flex items-center justify-between gap-2">
          <label class="text-xs font-medium text-gray-600">Шапка</label>
          <label class="flex cursor-pointer items-center gap-1.5">
            <input
              :checked="design.header_enabled"
              type="checkbox"
              class="rounded text-primary"
              @change="onHeaderEnabledChange"
            />
            <span class="text-xs">Показывать</span>
          </label>
        </div>
        <input
          :value="design.header_text"
          type="text"
          class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          placeholder="Текст шапки"
          @input="onHeaderTextInput"
        />
      </div>
      <div class="flex flex-col gap-2">
        <div class="flex items-center justify-between gap-2">
          <label class="text-xs font-medium text-gray-600">Подвал</label>
          <label class="flex cursor-pointer items-center gap-1.5">
            <input
              :checked="design.footer_enabled"
              type="checkbox"
              class="rounded text-primary"
              @change="onFooterEnabledChange"
            />
            <span class="text-xs">Показывать</span>
          </label>
        </div>
        <input
          :value="design.footer_text"
          type="text"
          class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          placeholder="Текст подвала"
          @input="onFooterTextInput"
        />
      </div>
    </div>

    <button
      type="button"
      class="mt-1 rounded-md border border-primary bg-white px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/5"
      @click="emitApplyToAll"
    >
      Применить ко всем слайдам
    </button>
  </div>
</template>

<script setup lang="ts">
import type { DesignSnapshot, DesignUpdate } from "~/types/design";

const props = defineProps<{
  design: DesignSnapshot;
}>();

const emit = defineEmits<{
  update: [payload: DesignUpdate];
  applyToAll: [];
}>();

const tabs = [
  { id: "template", label: "Шаблон" },
  { id: "background", label: "Фон" },
  { id: "layout", label: "Макет" },
  { id: "headerfooter", label: "Шапка & Подвал" },
] as const;

type TabId = (typeof tabs)[number]["id"];
const activeTab = ref<TabId>("template");

const templatePresets = [
  { id: "classic" as const, label: "Classic", stripColor: "#3e28c8" },
  { id: "bold" as const, label: "Bold", stripColor: "#bd2d36" },
  { id: "minimal" as const, label: "Minimal", stripColor: "#8664f9" },
];

const alignmentH = ["left", "center", "right"] as const;
const alignmentV = ["top", "center", "bottom"] as const;
const alignmentHLabels: Record<(typeof alignmentH)[number], string> = {
  left: "Слева",
  center: "Центр",
  right: "Справа",
};
const alignmentVLabels: Record<(typeof alignmentV)[number], string> = {
  top: "Верх",
  center: "Центр",
  bottom: "Низ",
};

const overlayPercent = computed(() => Math.round(props.design.overlay * 100));

const fileInputRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const { request } = useApi();

function emitUpdate(payload: DesignUpdate) {
  emit("update", payload);
}

function onBackgroundTypeChange(type: "color" | "image") {
  if (type === "color") {
    emit("update", {
      background: {
        type: "color",
        value: props.design.background_value?.startsWith("#") ? props.design.background_value : "#FFFFFF",
      },
    });
  } else {
    emit("update", { background: { type: "image" } });
  }
}

function onColorInput(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  emit("update", { background: { value: v } });
}

function onColorTextInput(e: Event) {
  const v = (e.target as HTMLInputElement).value.trim();
  if (!v) return;
  emit("update", { background: { value: v } });
}

function onOverlayInput(e: Event) {
  const pct = Number((e.target as HTMLInputElement).value);
  const overlay = pct / 100;
  emit("update", { background: { overlay } });
}

async function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploading.value = true;
  input.value = "";
  try {
    const form = new FormData();
    form.append("file", file);
    const data = await request<{ url: string; key: string }>("/api/v1/assets/upload", {
      method: "POST",
      body: form,
    });
    emit("update", {
      background: { type: "image", value: data.url },
    });
  } catch {
    // useApi shows toast on error
  } finally {
    uploading.value = false;
  }
}

function onPaddingInput(e: Event) {
  const v = Number((e.target as HTMLInputElement).value);
  emit("update", { layout: { padding: v } });
}

function onHeaderEnabledChange(e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  emit("update", { header: { enabled: checked } });
}

function onHeaderTextInput(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  emit("update", { header: { text: v } });
}

function onFooterEnabledChange(e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  emit("update", { footer: { enabled: checked } });
}

function onFooterTextInput(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  emit("update", { footer: { text: v } });
}

function emitApplyToAll() {
  emit("applyToAll");
}
</script>
