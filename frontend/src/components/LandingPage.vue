<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useSoloGameWebSocket } from '../composables/useSoloGameWebSocket.ts';
import { Filter } from 'bad-words';

const {
  initConnection,
  disconnect,
  isConnected,
  createGame,
  joinGame,
  currentError,
  playerName
} = useSoloGameWebSocket();

const filter = new Filter();
const nameError = ref('');

const joinInput = ref('');
const displayName = ref('');
const confirmedName = ref('');
const isNameConfirmed = ref(false);

const hasName = computed(() => displayName.value.trim().length > 0);
const isValidCode = computed(() => joinInput.value.length === 4);

const emit = defineEmits(['login']);

const handleLogin = () => {
  emit('login');
};

onMounted(() => {
  if (playerName.value) {
    displayName.value = playerName.value;

    if (isConnected.value) {
      confirmedName.value = playerName.value;
      isNameConfirmed.value = true;
    }
  }
});

const handleNameInput = () => {
  nameError.value = '';
  if (confirmedName.value && displayName.value === confirmedName.value) {
    isNameConfirmed.value = true;
    initConnection(displayName.value);
  } else {
    if (isNameConfirmed.value) disconnect();
    isNameConfirmed.value = false;
  }
};

const confirmName = () => {
  const rawName = displayName.value.trim();

  if (rawName.length < 3 || rawName.length > 15) {
    nameError.value = "Name must be between 3 and 12 characters.";
    return;
  }

  const validCharPattern = /^[a-zA-Z0-9 ]+$/;
  if (!validCharPattern.test(rawName)) {
    nameError.value = "Please use letters and numbers only.";
    return;
  }

  if (filter.isProfane(rawName)) {
    nameError.value = "That name is not allowed.";
    return;
  }

  nameError.value = '';
  confirmedName.value = rawName;
  isNameConfirmed.value = true;
  initConnection(rawName);
};

const handleCreate = () => {
  if (!isNameConfirmed.value) return;
  createGame(displayName.value);
};

const handleJoin = () => {
  if (!isNameConfirmed.value) {
    alert("Please confirm your display name first (click the arrow).");
    return;
  }
  if (!isValidCode.value) {
    alert("Please enter a valid 4-letter Game ID");
    return;
  }
  joinGame(joinInput.value, displayName.value);
};

const handleAbout = () => {
  alert("Ante Online: A real-time multiplayer card game.");
};
</script>

<template>
  <div class="landing-container">

    <header class="main-header">
      <div class="brand-logo"></div>
      <nav class="nav-links">
        <a href="#" @click.prevent="handleAbout" class="nav-item">About</a>
        <a href="#" @click.prevent="handleLogin" class="nav-item login-btn">Login</a>
      </nav>
    </header>

    <div class="content-box">
      <h1 class="title">ANTE <span class="badge">ONLINE</span></h1>

      <div v-if="isConnected" class="status-indicator">
        <div class="dot" :class="{ active: isConnected }"></div>
        <span>Connected</span>
      </div>

      <div class="input-group name-group">
        <label for="nickname">Display Name</label>

        <div class="input-wrapper">
          <input
            id="nickname"
            v-model="displayName"
            @input="handleNameInput"
            @keyup.enter="confirmName"
            type="text"
            placeholder="Enter your name..."
            class="text-input with-icon"
            maxlength="12"
          />

          <button
            @click="confirmName"
            class="icon-btn"
            :disabled="!hasName || (isNameConfirmed && isConnected)"
            :class="{ 'is-confirmed': isNameConfirmed }"
            title="Confirm Name"
          >
            <svg v-if="isNameConfirmed && isConnected" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="status-icon success">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>

            <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="status-icon action">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
            </svg>
          </button>
        </div>

        <div v-if="nameError" class="error-banner">
          {{ nameError }}
        </div>

      </div>

      <div v-if="isNameConfirmed && isConnected" class="actions">
        <div class="action-card create">
          <h2>Start Fresh</h2>
          <p>Create a new room and invite friends.</p>
          <button
            @click="handleCreate"
            :disabled="!isConnected || !isNameConfirmed"
            class="btn btn-primary"
          >
            Create New Game
          </button>
        </div>

        <div class="divider">OR</div>

        <div class="action-card join">
          <h2>Join Friend</h2>
          <p>Enter the 4-letter code.</p>

          <div class="join-row">
            <input
              v-model="joinInput"
              type="text"
              placeholder="CODE"
              maxlength="4"
              class="code-input"
            />
            <button
              @click="handleJoin"
              :disabled="!isConnected || !isValidCode || !isNameConfirmed"
              class="btn btn-secondary join-btn"
            >
              Join
            </button>
          </div>
          <div v-if="currentError" class="error-banner">
            {{ currentError }}
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.action-card h2 { color: #111827; font-size: 1.2rem; margin: 0 0 0.5rem 0; }
.action-card p { color: #6b7280; font-size: 0.9rem; margin: 0 0 1rem 0; }
.actions { display: flex; flex-direction: column; gap: 1.5rem; }
.badge { background: #facc15; border-radius: 20px; color: #854d0e; font-size: 0.9rem; letter-spacing: 0; padding: 4px 10px; vertical-align: middle; }
.brand-logo { color: white; font-size: 1.5rem; font-weight: 800; letter-spacing: -1px; opacity: 0.9; user-select: none; }
.btn { border: none; border-radius: 12px; cursor: pointer; font-size: 1rem; font-weight: bold; padding: 12px; transition: all 0.2s; }
.btn:active { transform: scale(0.98); }
.btn:disabled { background: #e5e7eb; box-shadow: none; color: #9ca3af; cursor: not-allowed; opacity: 0.5; }
.btn-primary { background: #1f2937; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); color: white; width: 100%; }
.btn-primary:hover:not(:disabled) { background: #374151; transform: translateY(-1px); }
.btn-secondary { background: #f3f4f6; border: 2px solid #f3f4f6; color: #374151; }
.btn-secondary:hover:not(:disabled) { background: #e5e7eb; border-color: #e5e7eb; }
.code-input { border: 2px solid #e5e7eb; border-radius: 12px; flex: 1; font-size: 1.2rem; font-weight: 700; min-width: 0; outline: none; padding: 12px; text-align: center; text-transform: uppercase; }
.code-input:focus { border-color: #1f2937; }
.content-box { background: white; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); max-width: 450px; padding: 2.5rem; text-align: center; width: 100%; }
.divider { color: #d1d5db; font-size: 0.8rem; font-weight: bold; letter-spacing: 1px; position: relative; }
.dot { background: #ef4444; border-radius: 50%; height: 8px; transition: background 0.3s; width: 8px; }
.dot.active { background: #22c55e; }
.error-banner { background: #fee2e2; border-radius: 8px; color: #991b1b; font-size: 0.9rem; font-weight: 600; margin-top: 20px; padding: 12px; text-align: center; }
.icon-btn { align-items: center; background: none; border: none; border-radius: 50%; cursor: pointer; display: flex; justify-content: center; padding: 5px; position: absolute; right: 8px; top: 50%; transform: translateY(-50%); transition: background 0.2s; }
.icon-btn:disabled { cursor: default; }
.icon-btn:hover:not(:disabled) { background: #f3f4f6; }
.input-group { margin-bottom: 2rem; text-align: left; }
.input-group label { color: #4b5563; display: block; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 0.5rem; text-transform: uppercase; }
.input-wrapper { align-items: center; display: flex; position: relative; }
.join-btn { min-width: 100px; width: auto; }
.join-row { display: flex; gap: 10px; width: 100%; }
.landing-container { align-items: center; background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%); display: flex; flex-direction: column; font-family: 'Segoe UI', sans-serif; justify-content: center; min-height: 100vh; padding: 1rem; position: relative; }
.main-header { align-items: center; box-sizing: border-box; display: flex; justify-content: space-between; left: 0; padding: 1.5rem 2rem; position: absolute; top: 0; width: 100%; z-index: 10; }
.nav-item { color: #9ca3af; font-size: 0.95rem; font-weight: 600; text-decoration: none; transition: color 0.2s ease; }
.nav-item.login-btn { border: 1px solid #4b5563; border-radius: 8px; color: white; padding: 6px 16px; }
.nav-item.login-btn:hover { background: rgba(255,255,255,0.1); border-color: white; }
.nav-item:hover { color: white; }
.nav-links { align-items: center; display: flex; gap: 2rem; }
.status-icon { height: 24px; transition: all 0.2s ease; width: 24px; }
.status-icon.action { color: #000; }
.status-icon.success { color: #22c55e; }
.status-indicator { align-items: center; color: #6b7280; display: flex; font-size: 0.85rem; gap: 8px; justify-content: center; margin-bottom: 2rem; }
.text-input { border: 2px solid #e5e7eb; border-radius: 12px; box-sizing: border-box; font-size: 1.1rem; outline: none; padding: 12px; padding-right: 50px; transition: border-color 0.2s; width: 100%; }
.text-input:focus { border-color: #1f2937; }
.title { color: #1f2937; font-size: 2.5rem; font-weight: 800; letter-spacing: -2px; margin: 0 0 1rem 0; }
</style>
