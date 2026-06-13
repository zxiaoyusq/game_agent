import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // 把所有 /api 请求转发到本地 FastAPI 后端，避免开发态跨域
    // 生产部署时通常通过 nginx 把 /api 反代到后端，前端打包输出无需感知此配置
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
