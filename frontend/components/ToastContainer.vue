<template>
  <Transition name="toast">
    <div
      v-if="isVisible && message"
      class="fixed bottom-4 left-4 right-4 z-50 mx-auto flex max-w-md items-start justify-between gap-2 rounded-lg bg-red-600 px-4 py-3 text-white shadow-lg sm:left-auto sm:right-4"
      role="alert"
    >
      <span>{{ message }}</span>
      <button
        type="button"
        @click="clear()"
        class="ml-4 shrink-0 font-bold opacity-80 hover:opacity-100"
        aria-label="Закрыть уведомление"
      >
        ×
      </button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
const { message, isVisible, clear } = useToast();
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}
</style>
