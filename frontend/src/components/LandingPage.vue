<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useGameWebSocket } from '../composables/useGameWebSocket.ts';

const {
  initConnection,
  disconnect,
  isConnected,
  createGame,
  joinGame,
  currentError,
  playerName //
} = useGameWebSocket();

const joinInput = ref('');
const displayName = ref('');
const confirmedName = ref('');
const isNameConfirmed = ref(false);

const hasName = computed(() => displayName.value.trim().length > 0);
const isValidCode = computed(() => joinInput.value.length === 4);

// Sync local state with global store on load
onMounted(() => {
  if (playerName.value) {
    displayName.value = playerName.value;

    // If we are already connected, lock the UI in "Confirmed" state
    if (isConnected.value) {
      confirmedName.value = playerName.value;
      isNameConfirmed.value = true;
    }
  }
});

const handleNameInput = () => {
  if (confirmedName.value && displayName.value === confirmedName.value) {
    isNameConfirmed.value = true;
    initConnection(displayName.value);
  } else {
    if (isNameConfirmed.value) disconnect();
    isNameConfirmed.value = false;
  }
};

const confirmName = () => {
  if (displayName.value.trim().length > 0) {
    confirmedName.value = displayName.value;
    isNameConfirmed.value = true;
    initConnection(displayName.value);
  }
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
</script>

<template>
  <div class="landing-container">

    <div class="content-box">
      <h1 class="title">UNO <span class="badge">ONLINE</span></h1>

      <div v-if="currentError" class="error-banner">
        {{ currentError }}
      </div>

      <div class="status-indicator">
        <div class="dot" :class="{ active: isConnected }"></div>
        <span>{{ isConnected ? 'Server Online' : 'Connecting...' }}</span>
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
            <svg v-if="isNameConfirmed" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="status-icon success">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>

            <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="status-icon action">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
            </svg>
          </button>
        </div>
      </div>

      <div class="actions">
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
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.landing-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e11d48 0%, #be123c 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Segoe UI', sans-serif;
  padding: 1rem;
}

.content-box {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.2);
  width: 100%;
  max-width: 450px;
  text-align: center;
}

.title {
  font-size: 2.5rem;
  margin: 0 0 1rem 0;
  color: #1f2937;
  font-weight: 800;
  letter-spacing: -2px;
}

.badge {
  background: #facc15;
  color: #854d0e;
  font-size: 0.9rem;
  padding: 4px 10px;
  border-radius: 20px;
  vertical-align: middle;
  letter-spacing: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 2rem;
  color: #6b7280;
  font-size: 0.85rem;
}

.dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  transition: background 0.3s;
}

.dot.active { background: #22c55e; }

.input-group {
  text-align: left;
  margin-bottom: 2rem;
}

.input-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  color: #4b5563;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.text-input {
  width: 100%;
  padding: 12px;
  padding-right: 50px;
  font-size: 1.1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.text-input:focus {
  border-color: #1f2937;
}

.icon-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.icon-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.icon-btn:disabled {
  cursor: default;
}

.status-icon {
  width: 24px;
  height: 24px;
  transition: all 0.2s ease;
}

.status-icon.action {
  color: #000;
}

.status-icon.success {
  color: #22c55e;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.divider {
  font-weight: bold;
  color: #d1d5db;
  position: relative;
  font-size: 0.8rem;
  letter-spacing: 1px;
}

.action-card h2 {
  font-size: 1.2rem;
  margin: 0 0 0.5rem 0;
  color: #111827;
}

.action-card p {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0 0 1rem 0;
}

.btn {
  padding: 12px;
  font-size: 1rem;
  font-weight: bold;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:active { transform: scale(0.98); }
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
}

.btn-primary {
  background: #1f2937;
  color: white;
  width: 100%;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.btn-primary:hover:not(:disabled) {
  background: #374151;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 2px solid #f3f4f6;
}
.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #e5e7eb;
}

.join-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.code-input {
  flex: 1;
  padding: 12px;
  text-align: center;
  font-size: 1.2rem;
  font-weight: 700;
  text-transform: uppercase;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  outline: none;
  min-width: 0;
}

.code-input:focus { border-color: #1f2937; }

.join-btn {
  width: auto;
  min-width: 100px;
}

.error-banner {
  background: #fee2e2;
  color: #991b1b;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}
</style>
