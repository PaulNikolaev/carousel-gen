<template>
  <div class="min-h-screen bg-gray-50">
    <header class="border-b border-gray-200 bg-white">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        <NuxtLink to="/" class="text-lg font-semibold text-gray-900">
          Carousels MVP
        </NuxtLink>
        <div class="flex gap-4">
          <NuxtLink
            to="/"
            class="text-gray-600 hover:text-gray-900"
            active-class="text-gray-900 font-medium"
          >
            Главная
          </NuxtLink>
        </div>
      </nav>
    </header>
    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <slot />
    </main>
  </div>
</template>
