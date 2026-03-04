export default defineNuxtConfig({
  compatibilityDate: "2025-03-04",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss"],
  runtimeConfig: {
    apiBaseUrl: "http://backend:8000",
    public: {
      apiBaseUrl: "http://localhost:8000",
    },
  },
});
