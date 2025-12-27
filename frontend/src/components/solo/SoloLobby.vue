<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSoloGameWebSocket } from '@/composables/useSoloGameWebSocket.ts';
import { fetchFromAPI } from "@/utils/api.ts";
import type {SoloGameSettings} from "@/types.ts";

const route = useRoute();
const router = useRouter();

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
  gameState,
  initConnection,
  joinGame,
  saveGameSettings,
  leaveGame,
  startGame
} = useSoloGameWebSocket();

const showNotification = ref<boolean>(false);
const showSettingsModal = ref<boolean>(false);
const settingsError = ref<string>('');
const settingsChanges = ref<SoloGameSettings>({});
const isReconnecting = ref(false);


onMounted(async () => {
  settingsChanges.value = JSON.parse(JSON.stringify(gameSettings.value));
  const routeId = route.params.id as string;

  if (isConnected.value && gameState.value === 'LOBBY') {
    console.log("Player is connected.")
    isReconnecting.value = false;
    return;
  }

  // 2. If disconnected, start recovery
  if (!isConnected.value) {
    console.log("Lobby: No connection. Reconnecting...");
    isReconnecting.value = true;
    try {
      const profile = await fetchFromAPI('/users/me');
      if (profile && profile.username) {
        initConnection(profile.username);
      }
    } catch (e) {
      console.error("Lobby Reconnection Failed:", e);
      await router.push('/dashboard');
    }
  }
  // 3. Connected but maybe just landed here
  else if (routeId && currentGameId.value !== routeId) {
    joinGame(routeId);
  }
});

// --- Critical Fix: Watch Game State ---
// As soon as the game state becomes 'LOBBY', we know we have joined successfully.
// This overrides any stuck 'isReconnecting' flags.
watch(gameState, (newState) => {
  if (newState === 'LOBBY' || newState === 'PLAYING') {
    isReconnecting.value = false;
  }
});

// Watch connection to trigger join if we were reconnecting
watch(isConnected, (connected) => {
  if (connected && isReconnecting.value) {
    const routeId = route.params.id as string;
    if (routeId) {
      console.log("Lobby: Connection established. Now joining:", routeId);
      joinGame(routeId);
      // Note: We don't set isReconnecting=false here yet;
      // we wait for gameState to update to ensure data is loaded.
    }
  }
});

// Debugging for Host Status
watch(isHost, (val) => {
  console.log(`Am I Host? ${val} (Player: ${playerId.value}, Host: ${hostId.value})`);
});


// --- UI Logic ---

const copyCode = async () => {
  const codeToCopy = currentGameId.value || (route.params.id as string);
  if (!codeToCopy) return;

  let success = false;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try { await navigator.clipboard.writeText(codeToCopy); success = true; } catch (err) { console.warn(err); }
  }
  if (!success) {
    try {
      const textArea = document.createElement("textarea");
      textArea.value = codeToCopy;
      textArea.style.position = "fixed"; textArea.style.opacity = "0";
      document.body.appendChild(textArea); textArea.focus(); textArea.select();
      success = document.execCommand('copy');
      document.body.removeChild(textArea);
    } catch (err) { console.error(err); }
  }
  if (success) {
    showNotification.value = true;
    setTimeout(() => { showNotification.value = false; }, 3000);
  }
};

const getInitials = (name: string) => name ? name.substring(0, 1).toUpperCase() : '??';
const allPlayersReady = computed(() => players.value.length >= 2 && players.value.every(pId => playerStates.value[pId] === 'ready'));
const getStatusLabel = (playerId: string) => playerStates.value[playerId] === 'playing' ? 'Playing' : 'Ready';

watch(showSettingsModal, (isOpen) => { if (isOpen) settingsChanges.value = JSON.parse(JSON.stringify(gameSettings.value)); });

const saveSettings = () => {
  if (!isHost.value) return;
  // Simplified check: only block if actively playing, waiting/lobby is fine
  if (gameState.value === 'PLAYING') {
      settingsError.value = 'Cannot update settings while a game is in progress.';
      setTimeout(() => { settingsError.value = ''; }, 4000);
      return;
  }
  gameSettings.value = JSON.parse(JSON.stringify(settingsChanges.value));
  saveGameSettings();
  showSettingsModal.value = false;
};

const handleLeave = () => {
  leaveGame();
  router.push('/solo');
};
</script>

<template>
  <div class="lobby-container">
    <Transition name="toast">
      <div v-if="showNotification" class="copy-notification">
        <span>Lobby Code Copied!</span>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showSettingsModal" class="modal-backdrop" @click.self="showSettingsModal = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Game Rules</h3>
            <button class="btn-close" @click="showSettingsModal = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="setting-row">
              <label>Turn Timer ({{ settingsChanges.turnTimer }}s)</label>
              <input type="range" v-model.number="settingsChanges.turnTimer" min="5" max="60" step="5" class="slider" :disabled="!isHost">
            </div>
            <div class="setting-row">
              <label>Stacking Rules</label>
              <select v-model="settingsChanges.stackingMode" class="select-input" :disabled="!isHost">
                <option value="off">No Stacking</option>
                <option value="standard">Standard (+2 on +2)</option>
                <option value="aggressive">Aggressive (Any + card)</option>
              </select>
            </div>
            <div class="setting-row">
              <label>AFK Penalty</label>
              <select v-model="settingsChanges.afkBehavior" class="select-input" :disabled="!isHost">
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
                <input type="checkbox" v-model="settingsChanges.forfeitAfterSkips" :disabled="!isHost">
                <span class="slider-toggle"></span>
              </label>
            </div>
            <div v-if="settingsError" class="settings-error"><p>{{ settingsError }}</p></div>
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

    <div v-if="isReconnecting && !isConnected" class="connection-warning">
      <div class="mini-spinner dark-spinner"></div> Connecting to Game Server...
    </div>

    <div class="lobby-card">
      <div class="lobby-header">
        <div class="header-content">
          <h2>Game Lobby</h2>
          <p class="subtext">Waiting for players to join...</p>
        </div>
        <div class="header-right">
           <button class="settings-btn" @click="showSettingsModal = true" title="Game Settings">⚙️</button>
          <div class="room-code-box" @click="copyCode" title="Click to Copy">
            <div class="code-label">ENTRY CODE</div>
            <div class="code-row">
              <span class="code">{{ currentGameId || route.params.id }}</span>
              <span class="copy-icon">❐</span>
            </div>
          </div>
        </div>
      </div>

      <div class="player-grid-container">
        <TransitionGroup name="list" tag="div" class="player-grid">
          <div v-for="pId in players" :key="pId" class="player-card" :class="{ 'is-me': pId === playerId, 'is-host': pId === hostId }">
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

        <div v-if="players.length === 0" class="loading-state">
           <div class="pulse-ring"></div>
           <span>Loading Room Data...</span>
        </div>
        <div v-else-if="players.length < 2" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>Waiting for friends...</span>
        </div>
      </div>

      <div class="lobby-footer">
        <button class="btn btn-leave" @click="handleLeave">Leave</button>
        <div class="right-actions">
          <div v-if="!isHost" class="waiting-for-host">Host will start the game<div class="mini-spinner"></div></div>
          <button v-if="isHost" class="btn btn-start" :disabled="players.length < 2 || !allPlayersReady" @click="startGame">Start Game</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Reuse existing styles */
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
.connection-warning { background: #facc15; color: #854d0e; font-weight: bold; padding: 10px; position: fixed; text-align: center; top: 0; width: 100%; z-index: 2000; display: flex; justify-content: center; gap: 10px; align-items: center; }
.dark-spinner { border-color: #854d0e; border-top-color: transparent; }
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
.toast-enter-active, .toast-leave-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -20px); }
.waiting-for-host { align-items: center; color: #64748b; display: flex; font-size: 0.9rem; font-style: italic; font-weight: 500; gap: 8px; }
.waiting-state { align-items: center; color: #94a3b8; display: flex; flex-direction: column; font-weight: 500; gap: 1rem; margin-top: 3rem; opacity: 0.8; }
.loading-state { align-items: center; color: #94a3b8; display: flex; flex-direction: column; font-weight: 500; gap: 1rem; margin-top: 3rem; opacity: 0.8; }
.waiting-warning { color: #eab308; font-size: 0.85rem; font-weight: 700; }
@keyframes ping { 75%, 100% { opacity: 0; transform: scale(2); } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.settings-error { text-align: center; color: #ef4444; font-weight: 700; }
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
.badge-readonly { font-size: 0.65rem; text-transform: uppercase; font-weight: 800; background: #e2e8f0; color: #64748b; padding: 2px 8px; border-radius: 6px; align-self: flex-start; }
.btn-close { background: transparent; border: none; font-size: 1.5rem; color: #94a3b8; cursor: pointer; padding: 4px; line-height: 1; border-radius: 50%; transition: background 0.2s; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;}
.btn-close:hover { background: #e2e8f0; color: #ef4444; }
.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
.setting-row { display: flex; flex-direction: column; gap: 8px; }
.setting-row label { font-size: 0.9rem; font-weight: 700; color: #475569; }
.select-input { width: 100%; padding: 10px 12px; border-radius: 8px; border: 2px solid #e2e8f0; font-size: 1rem; color: #1e293b; background-color: white; outline: none; transition: border-color 0.2s; appearance: none; }
.select-input:focus { border-color: #38bdf8; }
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
.toggle-row { flex-direction: row; justify-content: space-between; align-items: center; }
.toggle-text { display: flex; flex-direction: column; }
.sub-label { font-size: 0.75rem; color: #94a3b8; font-weight: 500; }
.switch { position: relative; display: inline-block; width: 48px; height: 26px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider-toggle { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #e2e8f0; transition: .4s; border-radius: 34px; }
.slider-toggle:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
input:checked + .slider-toggle { background-color: #10b981; }
input:checked + .slider-toggle:before { transform: translateX(22px); }
input:disabled + .slider-toggle { background-color: #f1f5f9; cursor: not-allowed; }
input:disabled + .slider-toggle:before { background-color: #cbd5e1; }
</style>
