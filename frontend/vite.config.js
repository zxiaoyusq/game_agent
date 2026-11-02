import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendPort = process.env.BACKEND_PORT || '8003'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 24681,
    strictPort: true,
    // 工作台 API 与远程 MCP 共用后端；保留路径和认证头，MCP 由后端负责鉴权。
    // 生产部署时通常通过 nginx 把 /api 反代到后端，前端打包输出无需感知此配置
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
      },
      '/mcp': {
        target: `http://127.0.0.1:${backendPort}`,
        changeOrigin: true,
      },
    },
    // 允许固定前端域名和 cloudflared 临时隧道访问本 dev server。
    // 否则 Vite 会基于 Host 头返回 "Blocked request" 拒绝外部域名转发过来的请求。
    allowedHosts: ['pagent.ahagamecenter.com', '.trycloudflare.com'],
  },
})
