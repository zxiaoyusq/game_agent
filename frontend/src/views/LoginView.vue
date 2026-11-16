<script setup>
import { computed, ref } from 'vue'
import StudioIcon from '../components/StudioIcon.vue'
import { auth, login } from '../data/auth.js'

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const canSubmit = computed(() => !!username.value.trim() && !!password.value && !auth.busy)

async function submit() {
  if (!canSubmit.value) return
  await login(username.value, password.value)
  if (auth.user) password.value = ''
}
</script>

<template>
  <main class="login-page">
    <a class="login-brand" href="/" aria-label="AHA 创造首页">
      <StudioIcon name="spark" :size="30" />
      <strong>AHA <span>创造</span></strong>
    </a>
    <section class="login-card" aria-labelledby="login-title">
      <span class="login-symbol"><StudioIcon name="game" :size="28" /></span>
      <h1 id="login-title">登录创作空间</h1>
      <p class="login-intro">从一个想法，做出你的下一款游戏。</p>
      <p v-if="!auth.ready" class="login-loading" role="status">正在检查登录状态…</p>
      <form v-else @submit.prevent="submit">
        <label for="login-username">用户名</label>
        <input id="login-username" v-model="username" name="username" autocomplete="username" placeholder="请输入用户名" maxlength="64" required :disabled="auth.busy" autofocus />
        <label for="login-password">密码</label>
        <div class="login-password">
          <input id="login-password" v-model="password" name="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="请输入密码" maxlength="512" required :disabled="auth.busy" />
          <button type="button" :aria-label="showPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showPassword" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button>
        </div>
        <p v-if="auth.error" class="login-error" role="alert">{{ auth.error }}</p>
        <button class="login-submit" type="submit" :disabled="!canSubmit" :aria-busy="auth.busy">
          {{ auth.busy ? '登录中…' : '登录' }}
          <StudioIcon v-if="!auth.busy" name="arrow" :size="18" />
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  padding: 100px 24px 60px;
  display: grid;
  align-content: center;
  justify-items: center;
  color: #dce9e4;
  background: radial-gradient(ellipse at 50% 40%, #203c3544, transparent 65%), #111719;
  color-scheme: dark;
}
.login-brand {
  position: absolute;
  top: 30px;
  left: 38px;
  display: flex;
  align-items: center;
  gap: 13px;
  color: #70d6bd;
}
.login-brand strong { font-size: 25px; font-weight: 700; letter-spacing: -.5px; }
.login-brand span { color: #dae7e2; font-size: 18px; margin-left: 5px; font-weight: 500; }
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 36px;
  background: #1a2223;
  border: 1px solid #789e8d2b;
  border-radius: 18px;
  box-shadow: 0 24px 80px #0003;
}
.login-symbol { display: grid; place-items: center; width: 54px; height: 54px; background: #70ceb414; border-radius: 14px; color: #83d7bc; margin-bottom: 24px; }
.login-card h1 { margin: 0; font-size: 25px; line-height: 1.4; font-weight: 600; }
.login-intro { margin: 10px 0 30px; font-size: 13px; color: #8ca79d; line-height: 1.8; }
.login-card label { display: block; font-size: 12px; color: #bccfc6; margin: 20px 0 9px; }
.login-card input { width: 100%; min-height: 46px; background: #131b1b; border: 1px solid #6c8c7e44; border-radius: 8px; color: #e1ede6; font: inherit; font-size: 14px; padding: 11px 13px; }
.login-card input::placeholder { color: #698276; }
.login-card input:focus { outline: 2px solid #70ceb489; outline-offset: 2px; }
.login-password { position: relative; }
.login-password input { padding-right: 62px; }
.login-password button { position: absolute; right: 6px; top: 6px; min-height: 34px; padding: 5px 10px; border-radius: 5px; color: #8ebaa5; font-size: 11px; }
.login-password button:focus-visible { outline: 2px solid #70ceb4; }
.login-error { margin: 16px 0 0; padding: 10px 12px; background: #9d563520; border: 1px solid #c98b6633; border-radius: 7px; color: #e8baa1; font-size: 12px; line-height: 1.7; overflow-wrap: anywhere; }
.login-submit { width: 100%; min-height: 46px; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 26px; background: #70ceb4; color: #12372b; border-radius: 8px; font-size: 14px; font-weight: 600; }
.login-submit:hover:not(:disabled) { background: #8bddc5; }
.login-submit:focus-visible { outline: 2px solid #b0efdb; outline-offset: 3px; }
.login-submit:disabled { opacity: .45; cursor: not-allowed; }
.login-loading { color: #92b6a6; font-size: 13px; }
@media (max-width: 500px) {
  .login-page { padding: 100px 20px 40px; }
  .login-brand { top: 24px; left: 24px; }
  .login-card { padding: 28px 24px; }
  .login-card input { font-size: 16px; }
}
</style>
