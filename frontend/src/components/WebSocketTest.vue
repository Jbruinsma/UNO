<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick } from 'vue';

// --- Types ---
type ConnectionStatus = 'Disconnected' | 'Connecting' | 'Connected';

interface LogMessage {
  id: number;
  direction: 'in' | 'out'; // To color code traffic
  text: string;
  timestamp: string;
}

// --- State ---
const status = ref<ConnectionStatus>('Disconnected');
const socket = ref<WebSocket | null>(null);
const logs = ref<LogMessage[]>([]);
const logContainer = ref<HTMLElement | null>(null);

// Form Inputs
const playerName = ref('Player-1');
const gameIdToJoin = ref('');
const activeGameId = ref<string | null>(null); // Stores ID if we are in a game

// --- Computed Helpers ---
const isConnected = computed(() => status.value === 'Connected');
const statusColor = computed(() => {
  if (status.value === 'Connected') return 'color: #10b981'; // Green
  if (status.value === 'Connecting') return 'color: #f59e0b'; // Orange
  return 'color: #ef4444'; // Red
});

// --- WebSocket Logic ---
const connect = () => {
  if (!playerName.value) return alert("Please enter a name");

  status.value = 'Connecting';
  // Note: We use the name in the URL to identify the connection immediately
  socket.value = new WebSocket(`ws://localhost:8000/ws/${playerName.value}`);

  socket.value.onopen = () => {
    status.value = 'Connected';
    addLog('System', 'Connection established');
  };

  socket.value.onmessage = (event) => {
    addLog('in', event.data);

    // Auto-parse JSON to see if we joined a game
    try {
      const data = JSON.parse(event.data);
      if (data.event === "game_created" || data.event === "game_joined") {
        activeGameId.value = data.game_id;
      }
    } catch (e) {
      // Not JSON, ignore specific parsing
    }
  };

  socket.value.onclose = () => {
    status.value = 'Disconnected';
    activeGameId.value = null;
    addLog('System', 'Disconnected');
  };
};

const disconnect = () => {
  if (socket.value) socket.value.close();
};

// --- Game Actions ---
const createGame = () => {
  sendJson({ action: 'create_game' });
};

const joinGame = () => {
  if (!gameIdToJoin.value) return alert("Enter a Game ID");
  sendJson({
    action: 'join_game',
    game_id: gameIdToJoin.value
  });
};

const sendJson = (payload: object) => {
  if (!socket.value) return;
  const msg = JSON.stringify(payload);
  socket.value.send(msg);
  addLog('out', msg);
};

// --- Logging Helper ---
const addLog = (direction: 'in' | 'out' | 'System', text: string) => {
  logs.value.push({
    id: Date.now(),
    direction: direction as any,
    text,
    timestamp: new Date().toLocaleTimeString()
  });

  // Auto-scroll to bottom
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
};

onUnmounted(() => {
  disconnect();
});
</script>

<template>
  <div class="dashboard">
    <header>
      <h1>UNO Network Debugger</h1>
      <div class="status-badge">
        Status: <span :style="statusColor" class="status-text">{{ status }}</span>
      </div>
    </header>

    <div class="grid-layout">

      <div class="card">
        <h2>1. Identity</h2>
        <div class="control-group">
          <label>Player Name</label>
          <input v-model="playerName" :disabled="isConnected" type="text" placeholder="Enter Name" />
        </div>

        <div class="actions">
          <button v-if="!isConnected" @click="connect" class="btn-primary">Connect to Server</button>
          <button v-else @click="disconnect" class="btn-danger">Disconnect</button>
        </div>
      </div>

      <div class="card" :class="{ disabled: !isConnected }">
        <h2>2. Game Manager</h2>

        <div class="control-group">
          <label>New Match</label>
          <button @click="createGame" :disabled="!isConnected" class="btn-secondary">
            Create Game
          </button>
        </div>

        <hr />

        <div class="control-group">
          <label>Join Existing</label>
          <div class="input-row">
            <input v-model="gameIdToJoin" placeholder="Game ID (e.g. 1234)" />
            <button @click="joinGame" :disabled="!isConnected" class="btn-secondary">Join</button>
          </div>
        </div>

        <div v-if="activeGameId" class="active-game-banner">
          Current Room: <strong>{{ activeGameId }}</strong>
        </div>
      </div>

      <div class="card log-card">
        <h2>3. Network Traffic</h2>
        <div class="logs" ref="logContainer">
          <div v-for="log in logs" :key="log.id" class="log-entry" :class="log.direction">
            <span class="timestamp">[{{ log.timestamp }}]</span>
            <span class="tag">{{ log.direction.toUpperCase() }}</span>
            <span class="message">{{ log.text }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Reset & Base */
* { box-sizing: border-box; }

.dashboard {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background-color: #f4f4f9;
  min-height: 100vh;
  color: #333;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status-text { font-weight: bold; }

/* Grid Layout */
.grid-layout {
  display: grid;
  grid-template-columns: 1fr 1fr; /* Two columns for controls */
  gap: 20px;
}

/* Full width for logs on small screens, or span 2 cols */
.log-card {
  grid-column: span 2;
}

/* Cards */
.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  border: 1px solid #e5e7eb;
}

.card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

h2 {
  font-size: 1.1rem;
  margin-top: 0;
  border-bottom: 2px solid #f3f4f6;
  padding-bottom: 10px;
  margin-bottom: 15px;
  color: #4b5563;
}

/* Inputs & Buttons */
.control-group { margin-bottom: 15px; }
label { display: block; font-size: 0.9rem; margin-bottom: 5px; color: #6b7280; }
input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}

.input-row { display: flex; gap: 10px; }

button {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary { background: #3b82f6; color: white; }
.btn-primary:hover { background: #2563eb; }

.btn-secondary { background: #10b981; color: white; }
.btn-secondary:hover { background: #059669; }

.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover { background: #dc2626; }

.active-game-banner {
  margin-top: 15px;
  background: #dbeafe;
  color: #1e40af;
  padding: 10px;
  border-radius: 6px;
  text-align: center;
}

/* Logs */
.logs {
  background: #1f2937;
  color: #e5e7eb;
  height: 250px;
  overflow-y: auto;
  padding: 10px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.9rem;
}

.log-entry { margin-bottom: 6px; display: flex; gap: 10px; }
.log-entry.in .message { color: #60a5fa; } /* Blue for incoming */
.log-entry.out .message { color: #34d399; } /* Green for outgoing */

.tag { font-weight: bold; width: 35px; }
.timestamp { color: #9ca3af; }
</style>
