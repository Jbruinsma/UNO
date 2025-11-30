<script setup lang="ts">
import { useGameWebSocket } from '../composables/useGameWebSocket.ts';

const {
  currentGameId,
  players,
  playerNames,
  playerId,
  hostId,
  isHost,
  leaveGame,
  startGame
} = useGameWebSocket();

const copyCode = () => {
  if (currentGameId.value) {
    navigator.clipboard.writeText(currentGameId.value);
    alert("Code copied to clipboard!");
  }
};

const getInitials = (name: string) => {
  return name ? name.substring(0, 2).toUpperCase() : '??';
};
</script>

<template>
  <div class="lobby-container">
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
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="copy-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5A3.375 3.375 0 0 0 6.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0 0 15 2.25h-1.5a2.251 2.251 0 0 0-2.15 1.586m5.8 0c.065.21.1.433.1.664v.75h-6V4.5c0-.231.035-.454.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="player-grid-container">
        <TransitionGroup name="list" tag="div" class="player-grid">

          <div
            v-for="pId in players"
            :key="pId"
            class="player-card"
            :class="{
              'is-me': pId === playerId,
              'is-host': pId === hostId
            }"
          >
            <div v-if="pId === hostId" class="crown-icon" title="Host">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path fill-rule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clip-rule="evenodd" />
              </svg>
            </div>

            <div class="avatar">
              {{ getInitials(playerNames[pId]) }}
            </div>

            <div class="player-info">
              <span class="name">{{ playerNames[pId] }}</span>
              <span v-if="pId === playerId" class="me-tag">YOU</span>
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
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="btn-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75" />
          </svg>
          Leave
        </button>

        <div class="right-actions">
          <div v-if="!isHost" class="waiting-for-host">
            Host will start the game
          </div>

          <button
            v-if="isHost"
            class="btn btn-start"
            :disabled="players.length < 2"
            @click="startGame"
          >
            Start Game
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="btn-icon right">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.lobby-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Segoe UI', sans-serif;
  padding: 1rem;
}

.lobby-card {
  background: #f8fafc;
  width: 100%;
  max-width: 650px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* --- Header --- */
.lobby-header {
  background: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.header-content h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #0f172a;
  font-weight: 800;
}

.subtext {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.room-code-box {
  background: #0f172a;
  color: white;
  padding: 8px 16px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.room-code-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  background: #1e293b;
}

.room-code-box:active { transform: scale(0.96); }

.code-label {
  font-size: 0.6rem;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.code-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 2px;
  line-height: 1;
}

.copy-icon { width: 18px; height: 18px; color: #38bdf8; }


/* --- Player Grid --- */
.player-grid-container {
  padding: 2rem;
  background: #f1f5f9;
  flex-grow: 1;
  min-height: 300px;
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.2rem;
}

/* THE PLAYER CARD STYLE */
.player-card {
  background: white;
  padding: 1.2rem;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  position: relative;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

/* Hover Effect */
.player-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

/* Current User Styling */
.player-card.is-me {
  border-color: #38bdf8; /* Blue border */
  background: #f0f9ff;
}

/* Host Styling (Optional subtle border) */
.player-card.is-host {
  /* border-color: #facc15; */
}

/* Crown Icon */
.crown-icon {
  position: absolute;
  top: -10px;
  right: -10px;
  background: #facc15;
  color: #854d0e;
  width: 28px;
  height: 28px;
  padding: 4px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transform: rotate(15deg);
  z-index: 10;
}

/* Avatar Styling */
.avatar {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  box-shadow: inset 0 2px 4px rgba(255,255,255,0.3);
}

.player-card.is-me .avatar {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); /* Blue gradient for Me */
}

.player-card.is-host .avatar {
  border: 3px solid #facc15; /* Gold ring for Host */
}

/* Name & Info */
.player-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name {
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.me-tag {
  font-size: 0.65rem;
  font-weight: 800;
  color: #0ea5e9;
  background: rgba(14, 165, 233, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  align-self: center;
}

/* --- Waiting State --- */
.waiting-state {
  margin-top: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #94a3b8;
  font-weight: 500;
  opacity: 0.8;
}

.pulse-ring {
  width: 40px;
  height: 40px;
  border: 4px solid #cbd5e1;
  border-radius: 50%;
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

/* --- Footer --- */
.lobby-footer {
  padding: 1.5rem 2rem;
  background: white;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-icon { width: 20px; height: 20px; }

.btn-leave {
  background: white;
  color: #ef4444;
  border: 2px solid #fecaca;
}

.btn-leave:hover {
  background: #fef2f2;
  border-color: #ef4444;
}

.btn-start {
  background: #10b981;
  color: white;
  box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
}

.btn-start:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.btn-start:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}

.waiting-for-host {
  color: #64748b;
  font-style: italic;
  font-size: 0.9rem;
  font-weight: 500;
}

/* --- List Transitions --- */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}

.list-leave-active {
  position: absolute; /* Ensures smooth removal flow */
}
</style>
