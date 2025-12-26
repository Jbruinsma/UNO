<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

// 1. Dynamic Game Type (e.g., 'SOLO', 'POKER')
const gameTypeId = (route.params.id as string) || 'SOLO';

// State
const currentUser = ref<string>('Player'); // Will be updated by system message if needed
const balance = ref<number>(1000.00); // You might want to fetch this from an API endpoint later
const isLoading = ref(true);
const privateCode = ref('');
const socket = ref<WebSocket | null>(null);
const connectionError = ref<string>('');

interface GameSession {
  sessionId: string;
  roomCode: string;
  hostUsername: string;
  currentPlayers: number;
  maxPlayers: number;
  buyInAmount: number;
  status: 'WAITING' | 'IN_PROGRESS';
}

const sessions = ref<GameSession[]>([]);

const isValidCode = computed(() => privateCode.value.length === 4);

// --- WebSocket Logic ---
const connectWebSocket = () => {
  const token = localStorage.getItem('token');

  if (!token) {
    console.error("No access token found. Redirecting to login.");
    router.push('/login');
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  // Adjust host if your API is on a different port in dev (e.g. localhost:8000)
  const host = 'localhost:8000';
  const wsUrl = `${protocol}://${host}/games/${gameTypeId}/ws?token=${token}`;

  console.log(`Connecting to ${wsUrl}`);
  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => {
    console.log("Connected to Lobby WebSocket");
    connectionError.value = '';
    // Optional: Request status update immediately
    sendMessage("status_check");
  };

  socket.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      switch (data.event) {
        case 'lobby_update':
          // Map backend data to frontend interface
          sessions.value = data.games.map((g: any) => ({
            sessionId: g.game_id,
            roomCode: g.game_id,
            hostUsername: g.host_name || 'Unknown',
            currentPlayers: g.player_count,
            maxPlayers: g.max_players || 4,
            buyInAmount: g.buy_in || 0,
            status: g.is_active ? 'IN_PROGRESS' : 'WAITING'
          }));
          isLoading.value = false;
          break;

        case 'game_created':
        case 'game_joined':
          console.log(`Joining game ${data.game_id}...`);
          // Navigate to the actual game component
          router.push(`/game/${gameTypeId}/${data.game_id}`);
          break;

        case 'system':
          console.log("System:", data.message);
          // Optional: Parse "Welcome [Username]" to set currentUser name
          if (data.message.startsWith("Welcome")) {
             const name = data.message.split(' ')[1];
             if(name) currentUser.value = name;
          }
          break;

        case 'error':
          console.error("Server Error:", data.message);
          alert(data.message); // Simple feedback for now
          break;
      }
    } catch (e) {
      console.error("Failed to parse websocket message", e);
    }
  };

  socket.value.onclose = (event) => {
    console.log("WebSocket Closed", event.code, event.reason);
    if (event.code === 1008) {
      alert("Session expired. Please log in again.");
      router.push('/auth/login');
    } else if (!event.wasClean) {
      connectionError.value = "Connection lost. Reconnecting...";
      // Simple reconnect logic could go here
    }
  };

  socket.value.onerror = (error) => {
    console.error("WebSocket Error:", error);
  };
};

const sendMessage = (action: string, payload: any = {}) => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    socket.value.send(JSON.stringify({ action, ...payload }));
  } else {
    console.warn("Socket not open. Cannot send message.");
  }
};

// --- Actions ---

const joinSession = (roomCode: string) => {
  if (!roomCode) return;
  console.log(`Requesting to join room ${roomCode}`);
  sendMessage("join_game", { game_id: roomCode });
};

const handleJoinPrivate = () => {
  if (!isValidCode.value) return;
  joinSession(privateCode.value.toUpperCase());
};

const createSession = () => {
  console.log("Requesting to create table...");
  sendMessage("create_game");
};

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
};

const goBack = () => {
  router.push('/dashboard');
};

// --- Lifecycle ---

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.close();
  }
});
</script>

<template>
  <div class="lobby-container">

    <header class="navbar">
      <div class="nav-left">
        <button @click="goBack" class="back-icon-btn" title="Back to Dashboard">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
        </button>

        <h1 class="brand">{{ gameTypeId.toUpperCase() }} <span class="badge">LOBBY</span></h1>
      </div>

      <div class="nav-right">
        <div class="balance-pill">
          <span class="currency-symbol">$</span>
          <span class="amount">{{ formatCurrency(balance).replace('$', '') }}</span>
        </div>
        <div class="user-pill">{{ currentUser }}</div>
      </div>
    </header>

    <main class="main-content">

      <div class="action-bar">
        <div class="title-group">
          <h2>Active Tables</h2>
          <p>Select a table or create your own.</p>
        </div>

        <div class="actions-right">
          <div class="code-input-group">
            <input
              v-model="privateCode"
              type="text"
              placeholder="CODE"
              maxlength="4"
              class="code-input"
              @keyup.enter="handleJoinPrivate"
            />
            <button
              @click="handleJoinPrivate"
              :disabled="!isValidCode"
              class="btn-code-join"
            >
              Join
            </button>
          </div>

          <div class="divider-vertical"></div>

          <button @click="createSession" class="btn-create">
            + Create Table
          </button>
        </div>
      </div>

      <div v-if="connectionError" class="error-banner">
        {{ connectionError }}
      </div>

      <div v-if="isLoading" class="loading">
        <div class="spinner"></div>
        <p>Connecting to Lobby...</p>
      </div>

      <div v-else-if="sessions.length === 0" class="empty-state">
        <p>No active tables found.</p>
        <p class="sub-text">Be the first to start a game!</p>
      </div>

      <div v-else class="sessions-grid">
        <div v-for="session in sessions" :key="session.sessionId" class="session-card">
          <div class="card-top">
            <span class="room-code">#{{ session.roomCode }}</span>
            <span class="buy-in">{{ formatCurrency(session.buyInAmount) }} Buy-in</span>
          </div>

          <div class="card-mid">
            <div class="info-row">
              <span class="label">HOST</span>
              <span class="value">{{ session.hostUsername }}</span>
            </div>
            <div class="info-row right-align">
              <span class="label">PLAYERS</span>
              <span class="value" :class="{'full': session.currentPlayers === session.maxPlayers}">
                {{ session.currentPlayers }} / {{ session.maxPlayers }}
              </span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" :style="{ width: (session.currentPlayers / session.maxPlayers * 100) + '%' }"></div>
            </div>
          </div>

          <button @click="joinSession(session.roomCode)" class="btn-join" :disabled="session.currentPlayers >= session.maxPlayers">
            {{ session.currentPlayers >= session.maxPlayers ? 'FULL' : 'JOIN TABLE' }}
          </button>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
/* Keeping your existing styles */
.lobby-container {
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
  min-height: 100vh;
  color: white;
  font-family: 'Segoe UI', sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left { display: flex; align-items: center; gap: 1rem; }

.back-icon-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.back-icon-btn:hover { background: #facc15; color: #854d0e; border-color: #facc15; transform: translateX(-2px); }
.back-icon-btn svg { width: 20px; height: 20px; }

.brand { font-weight: 800; font-size: 1.5rem; color: #fff; margin: 0; }
.badge { background: #facc15; color: #854d0e; font-size: 0.8rem; padding: 2px 8px; border-radius: 12px; vertical-align: middle; margin-left: 8px;}

.nav-right { display: flex; gap: 20px; align-items: center; }
.balance-pill { background: #1f2937; padding: 4px 4px 4px 16px; border-radius: 20px; border: 1px solid #374151; font-family: 'Courier New', monospace; color: #facc15; font-weight: bold; display: flex; gap: 10px; align-items: center; }
.amount { font-size: 1.1rem; padding-right: 12px;}
.user-pill { font-weight: 600; font-size: 1.1rem; }

.main-content { max-width: 1200px; margin: 0 auto; padding: 3rem 2rem; width: 100%; box-sizing: border-box; }

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 20px;
}
.title-group h2 { font-size: 2.5rem; margin: 0 0 0.5rem 0; font-weight: 700; }
.title-group p { color: #9ca3af; margin: 0; }

.actions-right { display: flex; align-items: center; gap: 1.5rem; }

.code-input-group {
  display: flex;
  background: #1f2937;
  padding: 4px;
  border-radius: 14px;
  border: 1px solid #374151;
}

.code-input {
  background: transparent;
  border: none;
  color: white;
  font-family: 'Courier New', monospace;
  font-weight: bold;
  font-size: 1.1rem;
  width: 80px;
  text-align: center;
  text-transform: uppercase;
  outline: none;
}
.code-input::placeholder { color: #4b5563; }

.btn-code-join {
  background: #374151;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 10px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-code-join:hover:not(:disabled) { background: #4b5563; }
.btn-code-join:disabled { opacity: 0.5; cursor: not-allowed; }

.divider-vertical { width: 1px; height: 40px; background: rgba(255,255,255,0.1); }

.btn-create {
  background: #facc15; color: #854d0e; border: none; padding: 12px 24px;
  border-radius: 12px; font-weight: bold; cursor: pointer; transition: transform 0.2s; font-size: 1rem;
  box-shadow: 0 4px 10px rgba(250, 204, 21, 0.2);
}
.btn-create:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(250, 204, 21, 0.3); }

.sessions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 2rem; }
.session-card {
  background: white; color: #1f2937; border-radius: 20px; padding: 1.5rem;
  display: flex; flex-direction: column; gap: 1rem; transition: transform 0.2s;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  position: relative; overflow: hidden;
}
.session-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }

.card-top { display: flex; justify-content: space-between; font-weight: 800; font-size: 1.2rem; border-bottom: 2px solid #f3f4f6; padding-bottom: 1rem; align-items: center; }
.room-code { color: #6b7280; font-family: 'Courier New', monospace; letter-spacing: -1px;}
.buy-in { color: #059669; background: #d1fae5; padding: 4px 8px; border-radius: 8px; font-size: 0.9rem; }
.card-mid { display: flex; flex-direction: column; gap: 0.5rem; margin: 0.5rem 0; }
.info-row { display: flex; justify-content: space-between; align-items: center; }
.label { font-size: 0.75rem; color: #9ca3af; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.value { font-weight: 700; font-size: 1rem; color: #1f2937; }
.value.full { color: #dc2626; }
.progress-bar-bg { width: 100%; height: 6px; background: #e5e7eb; border-radius: 3px; margin-top: 5px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: #4f46e5; border-radius: 3px; transition: width 0.3s ease; }

.btn-join { background: #1f2937; color: white; border: none; padding: 14px; border-radius: 12px; font-weight: bold; cursor: pointer; margin-top: auto; width: 100%; font-size: 1rem; transition: background 0.2s; }
.btn-join:hover:not(:disabled) { background: #374151; }
.btn-join:disabled { opacity: 0.5; cursor: not-allowed; background: #9ca3af; }

.empty-state { text-align: center; color: #9ca3af; margin-top: 4rem; padding: 2rem; background: rgba(255,255,255,0.05); border-radius: 20px; }
.sub-text { font-size: 0.9rem; margin-top: 0.5rem; }

.error-banner {
    background-color: #f87171; color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; font-weight: bold;
}
.loading { text-align: center; margin-top: 3rem; color: #9ca3af; }
.spinner { border: 4px solid rgba(255, 255, 255, 0.1); width: 36px; height: 36px; border-radius: 50%; border-left-color: #facc15; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .navbar { padding: 1rem; }
  .user-pill { display: none; }
  .action-bar { flex-direction: column; align-items: flex-start; gap: 1rem; }
  .actions-right { width: 100%; justify-content: space-between; }
  .code-input-group { flex: 1; }
  .btn-create { flex: 1; text-align: center; }
  .divider-vertical { display: none; }
}
</style>
