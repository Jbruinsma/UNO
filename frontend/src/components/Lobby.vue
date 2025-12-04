<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameWebSocket } from '../composables/useGameWebSocket';

const {
  currentGameId,
  players,
  playerNames,
  playerStates,
  gameSettings,
  playerId,
  hostId,
  isHost,
  isConnected,
  saveGameSettings,
  leaveGame,
  startGame
} = useGameWebSocket();

const showNotification = ref(false);
const showSettingsModal = ref(false);

const copyCode = async () => {
  if (!currentGameId.value) return;

  const textToCopy = currentGameId.value;
  let success = false;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(textToCopy);
      success = true;
    } catch (err) {
      console.warn('Clipboard API failed, trying fallback...', err);
    }
  }

  if (!success) {
    try {
      const textArea = document.createElement("textarea");
      textArea.value = textToCopy;

      textArea.style.top = "0";
      textArea.style.left = "0";
      textArea.style.position = "fixed";
      textArea.style.opacity = "0";

      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      success = document.execCommand('copy');
      document.body.removeChild(textArea);
    } catch (err) {
      console.error('Fallback copy failed', err);
    }
  }

  if (success) {
    showNotification.value = true;
    setTimeout(() => { showNotification.value = false; }, 3000);
  }
};

const getInitials = (name: string) => {
  return name ? name.substring(0, 1).toUpperCase() : '??';
};

const allPlayersReady = computed(() => {
  if (players.value.length < 2) return false;
  return players.value.every(pId => playerStates.value[pId] === 'ready');
});

const getStatusLabel = (playerId: string) => {
  const state = playerStates.value[playerId];
  if (state === 'playing') return 'Playing';
  return 'Ready';
};

const saveSettings = () => {
  if (isHost.value) {
    console.log("Saving settings:", gameSettings.value);
    saveGameSettings();
  }
  showSettingsModal.value = false;
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

    <Transition name="fade">
      <div v-if="showSettingsModal" class="modal-backdrop" @click.self="saveSettings">
        <div class="modal-card">
          <div class="modal-header">
            <div class="header-title-group">
              <h3>Game Rules</h3>
              <span v-if="!isHost" class="badge-readonly">View Only</span>
            </div>
            <button class="btn-close" @click="saveSettings">✕</button>
          </div>

          <div class="modal-body">
            <div class="setting-row">
              <label>Turn Timer ({{ gameSettings.turnTimer }}s)</label>
              <input
                type="range"
                v-model.number="gameSettings.turnTimer"
                min="5"
                max="60"
                step="5"
                class="slider"
                :disabled="!isHost"
              >
            </div>

            <div class="setting-row">
              <label>Stacking Rules</label>
              <select v-model="gameSettings.stackingMode" class="select-input" :disabled="!isHost">
                <option value="off">No Stacking</option>
                <option value="standard">Standard (+2 on +2)</option>
                <option value="aggressive">Aggressive (Any + card)</option>
              </select>
            </div>

            <div class="setting-row">
              <label>AFK Penalty</label>
              <select v-model="gameSettings.afkBehavior" class="select-input" :disabled="!isHost">
                <option value="draw_skip">Draw & Skip Turn</option>
                <option value="skip">Skip</option>
              </select>
            </div>

            <div class="setting-row toggle-row">
              <div class="toggle-text">
                <label>Strict Mode</label>
                <span class="sub-label">Forfeit after 3 skips</span>
              </div>
              <label class="switch">
                <input
                  type="checkbox"
                  v-model="gameSettings.forfeitAfterSkips"
                  :disabled="!isHost"
                >
                <span class="slider-toggle"></span>
              </label>
            </div>

          </div>

          <div class="modal-footer">
            <button v-if="isHost" class="btn btn-save" @click="saveSettings">Save & Update</button>

            <div v-else class="guest-footer">
              <span class="host-msg">Host controls settings</span>
              <button class="btn btn-secondary" @click="showSettingsModal = false">Close</button>
            </div>
          </div>
        </div>
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

        <div class="header-right">
           <button class="settings-btn" @click="showSettingsModal = true" title="Game Settings">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="settings-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>

          <div class="room-code-box" @click="copyCode" title="Click to Copy">
            <div class="code-label">ENTRY CODE</div>
            <div class="code-row">
              <span class="code">{{ currentGameId }}</span>
              <span class="copy-icon">❐</span>
            </div>
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
        <button class="btn btn-leave" @click="leaveGame">Leave</button>
        <div class="right-actions">
          <div v-if="!isHost" class="waiting-for-host">Host will start the game<div class="mini-spinner"></div></div>
          <div v-if="isHost && !allPlayersReady && players.length >= 2" class="waiting-warning">Wait for everyone to finish...</div>
          <button v-if="isHost" class="btn btn-start" :disabled="players.length < 2 || !allPlayersReady" @click="startGame">Start Game</button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* EXISTING STYLES ... */
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
.crown-icon { background: #1e293b; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: #854d0e; font-size: 1.2rem; height: 28px; padding: 4px; position: absolute; right: -10px; text-align: center; top: -10px; transform: rotate(15deg); width: 28px; z-index: 10; }
.header-content h2 { color: #0f172a; font-size: 1.5rem; font-weight: 800; margin: 0; }
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
.mini-spinner { animation: spin 1s linear infinite; border: 2px solid #cbd5e1; border-radius: 50%; border-top-color: #64748b; height: 14px; width: 14px; }
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
.waiting-for-host { align-items: center; color: #64748b; display: flex; font-size: 0.9rem; font-style: italic; font-weight: 500; gap: 8px; }
.waiting-state { align-items: center; color: #94a3b8; display: flex; flex-direction: column; font-weight: 500; gap: 1rem; margin-top: 3rem; opacity: 0.8; }
.waiting-warning { color: #eab308; font-size: 0.85rem; font-weight: 700; }

@keyframes ping { 75%, 100% { opacity: 0; transform: scale(2); } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* --- SETTINGS MODAL STYLES --- */
.header-right { display: flex; align-items: center; gap: 12px; }

.settings-btn { background: white; border: 2px solid #cbd5e1; border-radius: 12px; color: #64748b; cursor: pointer; padding: 8px; transition: all 0.2s; display: flex; align-items: center; justify-content: center; width: 48px; height: 48px; }
.settings-btn:hover { border-color: #94a3b8; color: #475569; transform: translateY(-2px); }
.settings-icon { width: 24px; height: 24px; }

.modal-backdrop { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.modal-card { background: white; border-radius: 24px; width: 90%; max-width: 400px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); overflow: hidden; animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1.5rem; border-bottom: 1px solid #f1f5f9; background: #f8fafc; }
.header-title-group { display: flex; flex-direction: column; gap: 4px; }
.modal-header h3 { margin: 0; font-size: 1.25rem; font-weight: 800; color: #0f172a; }

/* Read Only Badge */
.badge-readonly { font-size: 0.65rem; text-transform: uppercase; font-weight: 800; background: #e2e8f0; color: #64748b; padding: 2px 8px; border-radius: 6px; align-self: flex-start; }

.btn-close { background: transparent; border: none; font-size: 1.5rem; color: #94a3b8; cursor: pointer; padding: 4px; line-height: 1; border-radius: 50%; transition: background 0.2s; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;}
.btn-close:hover { background: #e2e8f0; color: #ef4444; }

.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
.setting-row { display: flex; flex-direction: column; gap: 8px; }
.setting-row label { font-size: 0.9rem; font-weight: 700; color: #475569; }

.select-input { width: 100%; padding: 10px 12px; border-radius: 8px; border: 2px solid #e2e8f0; font-size: 1rem; color: #1e293b; background-color: white; outline: none; transition: border-color 0.2s; appearance: none; }
.select-input:focus { border-color: #38bdf8; }
/* Disabled state for inputs */
.select-input:disabled { background-color: #f1f5f9; color: #94a3b8; border-color: #e2e8f0; cursor: not-allowed; }

.slider { -webkit-appearance: none; width: 100%; height: 6px; background: #e2e8f0; border-radius: 3px; outline: none; }
.slider:disabled { opacity: 0.6; cursor: not-allowed; }
.slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #38bdf8; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 2px solid white; }
.slider:disabled::-webkit-slider-thumb { background: #94a3b8; }

.modal-footer { padding: 1.5rem; background: #f8fafc; border-top: 1px solid #f1f5f9; display: flex; justify-content: flex-end; }
.btn-save { background: #0f172a; color: white; width: 100%; justify-content: center; }
.btn-save:hover { background: #1e293b; }

.guest-footer { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.host-msg { font-size: 0.8rem; color: #94a3b8; font-style: italic; }
.btn-secondary { background: white; border: 2px solid #e2e8f0; color: #64748b; padding: 12px 24px; border-radius: 12px; font-weight: 700; cursor: pointer; }
.btn-secondary:hover { background: #f1f5f9; color: #475569; }

/* --- NEW TOGGLE SWITCH STYLES --- */
.toggle-row { flex-direction: row; justify-content: space-between; align-items: center; }
.toggle-text { display: flex; flex-direction: column; }
.sub-label { font-size: 0.75rem; color: #94a3b8; font-weight: 500; }

.switch { position: relative; display: inline-block; width: 48px; height: 26px; }
.switch input { opacity: 0; width: 0; height: 0; }

.slider-toggle { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #e2e8f0; transition: .4s; border-radius: 34px; }
.slider-toggle:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }

input:checked + .slider-toggle { background-color: #10b981; }
input:checked + .slider-toggle:before { transform: translateX(22px); }

/* Disabled toggle state */
input:disabled + .slider-toggle { background-color: #f1f5f9; cursor: not-allowed; }
input:disabled + .slider-toggle:before { background-color: #cbd5e1; }
</style>
