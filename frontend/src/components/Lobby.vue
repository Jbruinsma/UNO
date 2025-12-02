<script setup lang="ts">
import {ref, computed} from 'vue';
import { useGameWebSocket } from '../composables/useGameWebSocket';

const {
  currentGameId,
  players,
  playerNames,
  playerStates,
  playerId,
  hostId,
  isHost,
  isConnected,
  leaveGame,
  startGame
} = useGameWebSocket();

const showNotification = ref(false);

const copyCode = () => {
  if (currentGameId.value) {
    navigator.clipboard.writeText(currentGameId.value);
    showNotification.value = true;
    setTimeout(() => { showNotification.value = false; }, 3000);
  }
};

const getInitials = (name: string) => {
  return name ? name.substring(0, 1).toUpperCase() : '??';
};

const allPlayersReady = computed(() => {
  if (players.value.length === 0) return false;
  return players.value.every(pId => playerStates.value[pId] === 'ready');
});

const getStatusLabel = (pId: string) => {
  const state = playerStates.value[pId];
  if (state === 'playing') return 'Playing';
  return 'Ready';
};

</script>

<template>
  <div class="lobby-container">

    <Transition name="toast">
      <div v-if="showNotification" class="copy-notification">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="toast-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0 1 18 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3 1.5 1.5 3-3.75" />
        </svg>
        <span>Lobby Code Copied!</span>
      </div>
    </Transition>

    <div v-if="!isConnected" class="connection-warning">
      Trying to reconnect...
    </div>

    <div class="lobby-card">

      <div class="lobby-header">
        <div class="header-content">
          <h2>Game Lobby</h2>
          <p class="subtext">Waiting for players to join...</p>
        </div>

        <div class="room-code-box" @click="copyCode" title="Click to Copy">
          <div class="code-label">ENTRY CODE</div>
          <div class="code-row">
            <span class="code">{{ currentGameId }}</span>
            <span class="copy-icon">❐</span>
          </div>
        </div>
      </div>

      <div class="player-grid-container">
        <TransitionGroup name="list" tag="div" class="player-grid">
          <div
            v-for="pId in players"
            :key="pId"
            class="player-card"
            :class="{ 'is-me': pId === playerId, 'is-host': pId === hostId }"
          >
            <div v-if="pId === hostId" class="crown-icon" title="Host">👑</div>

            <div class="avatar">{{ getInitials(playerNames[pId]) }}</div>

            <div class="player-info">
              <span class="name">{{ playerNames[pId] }}</span>
              <span v-if="pId === playerId" class="me-tag">YOU</span>
            </div>

            <div class="status-badge" :class="playerStates[pId] === 'ready' ? 'status-ready' : 'status-playing'">
              {{ getStatusLabel(pId) }}
            </div>
          </div>
        </TransitionGroup>

        <div v-if="players.length < 2" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>Waiting for friends...</span>
        </div>
      </div>

      <div class="lobby-footer">
        <button class="btn btn-leave" @click="leaveGame">
          Leave
        </button>

        <div class="right-actions">
          <div v-if="!isHost" class="waiting-for-host">
            Host will start the game
          </div>

          <div v-if="isHost && !allPlayersReady" class="waiting-warning">
            Wait for everyone to finish...
          </div>

          <button
            v-if="isHost"
            class="btn btn-start"
            :disabled="players.length < 2 || !allPlayersReady"
            @click="startGame"
          >
            Start Game
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.avatar { align-items: center; background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%); border-radius: 50%; box-shadow: inset 0 2px 4px rgba(255,255,255,0.3); color: white; display: flex; font-size: 1.5rem; font-weight: 700; height: 64px; justify-content: center; width: 64px; }
.btn { align-items: center; border: none; border-radius: 12px; cursor: pointer; display: inline-flex; font-size: 1rem; font-weight: 700; gap: 8px; padding: 12px 24px; transition: all 0.2s; }
.btn-leave { background: white; border: 2px solid #fecaca; color: #ef4444; }
.btn-leave:hover { background: #fef2f2; border-color: #ef4444; }
.btn-start { background: #10b981; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3); color: white; }
.btn-start:disabled { background: #cbd5e1; box-shadow: none; color: #94a3b8; cursor: not-allowed; }
.btn-start:hover:not(:disabled) { background: #059669; transform: translateY(-1px); }
.code { font-size: 1.5rem; font-weight: 800; letter-spacing: 2px; line-height: 1; }
.code-label { color: #94a3b8; font-size: 0.6rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 2px; }
.code-row { align-items: center; display: flex; gap: 8px; }
.connection-warning { background: #facc15; color: #854d0e; font-weight: bold; padding: 10px; position: fixed; text-align: center; top: 0; width: 100%; z-index: 2000; }
.copy-icon { color: #38bdf8; font-size: 1.2rem; }
.copy-notification { position: fixed; top: 24px; left: 50%; transform: translateX(-50%); background: #1e293b; color: white; padding: 12px 24px; border-radius: 50px; display: flex; align-items: center; gap: 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); z-index: 100; font-weight: 600; border: 1px solid rgba(255,255,255,0.1); }
.crown-icon { background: #facc15; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: #854d0e; font-size: 1.2rem; height: 28px; padding: 4px; position: absolute; right: -10px; text-align: center; top: -10px; transform: rotate(15deg); width: 28px; z-index: 10; }
.header-content h2 { color: #0f172a; font-size: 1.5rem; font-weight: 800; margin: 0; }
.icon-check { color: #4ade80; font-size: 1.2rem; }
.is-host .avatar { border: 3px solid #facc15; }
.is-me { background: #f0f9ff; border-color: #38bdf8; }
.is-me .avatar { background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); }
.list-enter-active, .list-leave-active, .list-move { transition: all 0.4s ease; }
.list-enter-from, .list-leave-to { opacity: 0; transform: scale(0.9) translateY(10px); }
.list-leave-active { position: absolute; }
.lobby-card { background: #f8fafc; border-radius: 24px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); display: flex; flex-direction: column; max-width: 650px; overflow: hidden; width: 100%; }
.lobby-container { align-items: center; background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%); display: flex; font-family: 'Segoe UI', sans-serif; justify-content: center; min-height: 100vh; padding: 1rem; }
.lobby-footer { align-items: center; background: white; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; padding: 1.5rem 2rem; }
.lobby-header { align-items: center; background: white; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; padding: 1.5rem 2rem; }
.me-tag { align-self: center; background: rgba(14, 165, 233, 0.1); border-radius: 10px; color: #0ea5e9; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; }
.name { color: #1e293b; font-size: 1rem; font-weight: 700; max-width: 140px; overflow: hidden; text-align: center; text-overflow: ellipsis; white-space: nowrap; }
.player-card { align-items: center; background: white; border: 2px solid transparent; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; gap: 12px; padding: 1.2rem; position: relative; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.player-card:hover { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transform: translateY(-4px); }
.player-grid { display: grid; gap: 1.2rem; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
.player-grid-container { background: #f1f5f9; flex-grow: 1; min-height: 300px; padding: 2rem; }
.player-info { display: flex; flex-direction: column; gap: 4px; text-align: center; }
.pulse-ring { animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; border: 4px solid #cbd5e1; border-radius: 50%; height: 40px; width: 40px; }
.right-actions { align-items: center; display: flex; gap: 1rem; }
.room-code-box { align-items: center; background: #0f172a; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); color: white; cursor: pointer; display: flex; flex-direction: column; padding: 8px 16px; transition: all 0.2s ease; }
.room-code-box:active { transform: scale(0.96); }
.room-code-box:hover { background: #1e293b; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transform: translateY(-2px); }
.status-badge { border-radius: 8px; font-size: 0.75rem; font-weight: 700; margin-top: auto; padding: 4px 10px; text-transform: uppercase; }
.status-playing { background: #fed7aa; color: #c2410c; }
.status-ready { background: #bbf7d0; color: #15803d; }
.subtext { color: #64748b; font-size: 0.9rem; margin: 0; }
.toast-icon { width: 24px; height: 24px; color: #4ade80; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -20px); }
.waiting-for-host { color: #64748b; font-size: 0.9rem; font-style: italic; font-weight: 500; }
.waiting-state { align-items: center; color: #94a3b8; display: flex; flex-direction: column; font-weight: 500; gap: 1rem; margin-top: 3rem; opacity: 0.8; }
.waiting-warning { color: #eab308; font-size: 0.85rem; font-weight: 700; }

@keyframes ping { 75%, 100% { opacity: 0; transform: scale(2); } }
</style>
