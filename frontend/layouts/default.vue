<template>
  <div class="min-h-screen bg-gray-50 font-sans">
    <header class="border-b border-gray-200 bg-white">
      <nav aria-label="Основная навигация" class="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-3 sm:px-6">
        <NuxtLink
          to="/"
          class="flex items-center gap-2 text-lg font-semibold text-accent transition-colors hover:text-accent/90"
        >
          <span
            class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded border-2 border-accent text-accent"
            aria-hidden="true"
          >
            <span class="text-sm">⊕</span>
          </span>
          Карусели
        </NuxtLink>
        <div class="flex flex-wrap gap-4">
          <NuxtLink
            to="/"
            class="text-gray-600 transition-colors hover:text-accent"
            exact-active-class="text-accent font-medium"
          >
            Список каруселей
          </NuxtLink>
          <NuxtLink
            to="/create"
            class="text-gray-600 transition-colors hover:text-accent"
            active-class="text-accent font-medium"
          >
            Создать карусель
          </NuxtLink>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <slot />
    </main>
    <ToastContainer />
  </div>
</template>
