import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { copyFileSync } from "node:fs";

export default defineConfig({
  base: "./",
  plugins: [
    vue(),
    {
      name: "native-panel-entry",
      closeBundle() {
        // 小程序使用 index.html；模板 app.json 使用 MainPage.html，两种宿主共享同一构建入口。
        copyFileSync("dist/index.html", "dist/MainPage.html");
      }
    }
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    dedupe: ["vue", "vue-i18n", "vue-router"]
  },
  optimizeDeps: { exclude: ["xjiang-sdk", "xjiang-ui"] },
  // 模板 SDK 会打印宿主消息与 WebSocket URL；发布包去除这些日志，避免输出临时授权。
  esbuild: { drop: ["console", "debugger"] },
  build: { sourcemap: false, target: "es2020" }
});
