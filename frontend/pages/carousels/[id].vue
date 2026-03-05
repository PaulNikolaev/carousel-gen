<template>
  <div>
    <h1 class="text-3xl font-bold text-gray-900">
      Редактор карусели
    </h1>
    <p class="mt-2 text-gray-600">
      Генерация и редактирование слайдов (заглушка). ID: {{ id }}
    </p>
  </div>
</template>

<script setup lang="ts">
const route = useRoute();
const id = computed(() => route.params.id as string);
</script>
