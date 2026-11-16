<script setup>
import { ref } from 'vue'
import { auth, logout } from '../data/auth.js'

const busy = ref(false)
const error = ref('')
async function signOut() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try { await logout() }
  catch { error.value = '退出未成功，请重试。' }
  finally { busy.value = false }
}
</script>

<template>
  <div class="user-menu" aria-label="当前登录账号">
    <span class="user-avatar">{{ auth.user?.username?.slice(0, 1).toUpperCase() }}</span>
    <span class="user-name">{{ auth.user?.username }}</span>
    <button :disabled="busy" @click="signOut">{{ busy ? '退出中…' : '退出登录' }}</button>
    <span v-if="error" class="logout-error" role="alert">{{ error }}</span>
  </div>
</template>

<style scoped>
.user-menu { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 12px; }
.user-avatar { display: grid; place-items: center; width: 30px; height: 30px; border: 1px solid #c8d2be; border-radius: 50%; background: #e6eddf; color: #526b43; font-weight: 600; }
.user-name { color: #596b4e; }
.user-menu button { font-size: 11px; color: #637c53; padding: 6px 9px; border: 1px solid #d4deca; border-radius: 5px; }
.user-menu button:hover { background: #e8eedf; }
.user-menu button:focus-visible { outline: 2px solid #5278b8; outline-offset: 2px; }
.user-menu button:disabled { opacity: .5; cursor: wait; }
.logout-error { color: #a85842; font-size: 11px; }
</style>
