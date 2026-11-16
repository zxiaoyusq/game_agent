<script setup>
import { computed, onMounted } from 'vue'
import { loadProducedGames, producedGames } from '../data/producedGames.js'
import StudioIcon from './StudioIcon.vue'
const emit = defineEmits(['navigate'])
// 只展示真实可玩的作品，不用假封面或占位卡片冒充已交付游戏。
const games = computed(() =>
  producedGames.items
    .filter((item) => item.available && item.cover_url)
    .slice(0, 6),
)
onMounted(loadProducedGames)
</script>

<template>
  <section
    v-if="games.length || producedGames.error"
    class="creation-showcase"
    aria-label="已有游戏作品"
  >
    <div class="showcase-heading">
      <div>
        <span>MADE HERE</span>
        <h2>一些灵感，已经变成了游戏。</h2>
      </div>
      <button type="button" @click="emit('navigate', 'produced-games')">
        探索作品库
        <StudioIcon name="diagonal" :size="14" />
      </button>
    </div>
    <div v-if="games.length" class="showcase-games">
      <a
        v-for="game in games"
        :key="game.id"
        :href="game.play_url"
        target="_blank"
        rel="noopener"
        :aria-label="`试玩 ${game.name}（新窗口）`"
      >
        <div class="showcase-cover">
          <img :src="game.cover_url" :alt="game.name" loading="lazy" />
          <span>
            <StudioIcon name="game" :size="18" />
            试玩
          </span>
        </div>
        <h3>{{ game.name.split(' · ')[0] }}</h3>
        <p>{{ game.category }}</p>
      </a>
    </div>
    <p v-else class="showcase-error">
      作品暂时未加载。
      <button type="button" @click="loadProducedGames">重新加载</button>
    </p>
  </section>
</template>

<style scoped>
.creation-showcase {
  margin-top: 58px;
  padding-top: 34px;
  border-top: 1px solid #ffffff0b;
}
.showcase-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 23px;
}
.showcase-heading span {
  font-size: 9px;
  color: #757b89;
  letter-spacing: 2px;
}
.showcase-heading h2 {
  color: #d6d9e0;
  font-size: 17px;
  font-weight: 500;
  margin-top: 7px;
}
.showcase-heading button {
  color: #949aa7;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.showcase-games {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
}
.showcase-games a {
  color: inherit;
  min-width: 0;
}
.showcase-cover {
  height: 145px;
  border: 1px solid #ffffff12;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background: #20232b;
}
.showcase-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition:
    transform 0.35s ease,
    filter 0.35s ease;
  filter: saturate(0.8) brightness(0.9);
}
.showcase-cover > span {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  position: absolute;
  inset: 0;
  opacity: 0;
  background: #090d1966;
  color: white;
  font-size: 12px;
  transition: opacity 0.2s;
}
.showcase-games a:hover img {
  transform: scale(1.05);
  filter: saturate(1);
}
.showcase-games a:hover .showcase-cover > span,
.showcase-games a:focus-visible .showcase-cover > span {
  opacity: 1;
}
.showcase-games h3 {
  font-size: 12px;
  font-weight: 500;
  color: #b3b8c2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 11px;
}
.showcase-games p {
  font-size: 10px;
  color: #737986;
  margin-top: 3px;
}
.showcase-error {
  color: #9aa1af;
  font-size: 13px;
}
.showcase-error button {
  color: #5fd6c3;
  margin-left: 8px;
}
@media (max-width: 1050px) {
  .showcase-games {
    gap: 12px;
  }
  .showcase-cover {
    height: 125px;
  }
}
@media (max-width: 760px) {
  .creation-showcase {
    margin-top: 40px;
  }
  .showcase-games {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px 12px;
  }
  .showcase-heading h2 {
    font-size: 15px;
  }
  .showcase-heading button {
    font-size: 11px;
  }
  .showcase-cover {
    height: 140px;
  }
}
@media (max-width: 380px) {
  .showcase-cover {
    height: 108px;
  }
  .showcase-heading {
    align-items: start;
    flex-direction: column;
    gap: 12px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .showcase-cover img,
  .showcase-cover > span {
    transition: none;
  }
}
</style>
