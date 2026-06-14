import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  base: "/cau19/",
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    // 청크 크기 경고 임계값 높이기
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 벤더 라이브러리 분리 (캐싱 효율화)
        manualChunks: {
          "react-core":   ["react", "react-dom"],
          "recharts":     ["recharts"],
          "radix-ui":     [
            "@radix-ui/react-tabs",
            "@radix-ui/react-select",
            "@radix-ui/react-tooltip",
            "@radix-ui/react-toast",
            "@radix-ui/react-dialog",
            "@radix-ui/react-slot",
          ],
          "router":       ["wouter"],
          "utils":        ["clsx", "tailwind-merge", "class-variance-authority"],
        },
      },
    },
    // 소스맵 제거 (파일 크기 감소)
    sourcemap: false,
    // 압축 최적화
    minify: "esbuild",
    target: "es2020",
  },
  // 사용하지 않는 모듈 제거
  esbuild: {
    drop: ["console", "debugger"],  // 프로덕션에서 console.log 제거
    legalComments: "none",
  },
});
