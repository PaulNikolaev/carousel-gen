export default defineNuxtConfig({
  compatibilityDate: "2025-03-04",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss"],
  tailwindcss: {
    config: {
      theme: {
        extend: {
          colors: {
            accent: "#E4AF0A",
            primary: "#2563EB",
          },
          fontFamily: {
            sans: [
              "SF Pro Display",
              "SF Pro Text",
              "system-ui",
              "-apple-system",
              "sans-serif",
            ],
          },
          fontSize: {
            ui: ["13.5px", { lineHeight: "1.4" }],
          },
        },
      },
    },
  },
  runtimeConfig: {
    apiBaseUrl: "http://backend:8000",
    public: {
      apiBaseUrl: "http://localhost:8000",
    },
  },
});
