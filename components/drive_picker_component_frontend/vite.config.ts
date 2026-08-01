import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    outDir: "build",
    target: "es2022",
    sourcemap: true,
  },
});
