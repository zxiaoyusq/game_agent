<script setup>
// 创作台共用的线性图标，保持笔画、视口与对齐一致，不依赖外部图标服务。
defineProps({
  name: { type: String, default: 'spark' },
  size: { type: [Number, String], default: 20 },
})
const paths = {
  spark: 'm12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4L12 3Z',
  plus: 'M12 5v14M5 12h14',
  grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
  layers: 'm12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5',
  game: 'M8 7h8c3 0 5 3 5 7s-2 5-4 2l-1-1H8l-1 1c-2 3-4 2-4-2s2-7 5-7ZM8 10v4M6 12h4m6-1h.01M18 13h.01',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  diagonal: 'M6 18 18 6M6 6h12v12',
  back: 'M19 12H5m6-6-6 6 6 6',
  chevron: 'm8 10 4 4 4-4',
  image: 'M4 4h16v16H4zM4 16l5-5 4 4 3-3 4 4M15 8h.01',
  settings: 'M4 7h9m4 0h3M4 17h3m4 0h9M13 4v6M7 14v6',
  upload: 'M12 15V3m-4 4 4-4 4 4M4 14v6h16v-6',
  download: 'M12 3v12m-4-4 4 4 4-4M4 14v6h16v-6',
  code: 'm8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18',
  check: 'm5 12 4 4L19 6',
  clock: 'M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  menu: 'M4 6h16M4 12h16M4 18h16',
  close: 'm6 6 12 12M6 18 18 6',
  home: 'm3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7',
  refresh:
    'M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 12-1l2 6M4 12l2 6a7 7 0 0 0 12-1',
  desktop: 'M3 4h18v13H3zM8 21h8M12 17v4',
  phone: 'M7 2h10v20H7zM11 18h2',
  expand: 'M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5',
  pause: 'M8 5v14M16 5v14',
  play: 'm8 4 12 8-12 8V4Z',
  file: 'M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h5',
  alert: 'm12 3 10 18H2L12 3Zm0 6v5m0 3h.01',
}
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] || paths.spark" />
  </svg>
</template>
