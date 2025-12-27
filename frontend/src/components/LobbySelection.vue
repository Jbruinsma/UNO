<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSoloGameWebSocket } from '@/composables/useSoloGameWebSocket';
import { fetchFromAPI } from "@/utils/api.ts";
import CreateGameModal from '@/components/CreateGameModal.vue';
import type {Game, GameState} from "@/types.ts";

interface UserProfile {
  userId: string;
  username: string;
  email: string;
  birthday: string;
  currentBalance: string;
  createdAt: string;
}

const route = useRoute();
const router = useRouter();

const gameTypeId = (route.params.id as string)?.toUpperCase() || 'SOLO';

interface GameConnector {
  state: {
    availableGames: Game[];
    isConnected: boolean;
    error: string | null;
    gameState: GameState;
  };
  actions: {
    initConnection: (name: string) => void;
    disconnect: () => void;
    createGame: (options: { maxPlayers: number; buyIn: number }) => void;
    joinGame: (gameId: string, name: string) => void;
    statusCheck: () => void;
  };
}

const getGameConnector = (type: string): GameConnector | null => {
  switch (type) {
    case 'SOLO': {
      const solo = useSoloGameWebSocket();
      return {
        state: {
          get availableGames() { return solo.availableGames.value },
          get isConnected() { return solo.isConnected.value },
          get error() { return solo.currentError.value },
          get gameState() { return solo.gameState.value }
        },
        actions: {
          initConnection: solo.initConnection,
          disconnect: solo.disconnect,
          createGame: solo.createGame,
          joinGame: solo.joinGame,
          statusCheck: solo.statusCheck
        }
      };
    }
    default:
      console.error(`No composable found for game type: ${type}`);
      return null;
  }
};

const connector = getGameConnector(gameTypeId);

const showCreateModal = ref(false);
const currentUser = ref<string>('Player');
const balance = ref<number>(0.00);
const privateCode = ref('');
const isValidCode = computed(() => privateCode.value.length === 4);

const sessionToJoin = ref<{ roomCode: string; buyIn: number } | null>(null);

const sessions = computed(() => {
  if (!connector) return [];

  const games = [...connector.state.availableGames];

  games.sort((a, b) => {
    const buyInA = a.buyIn || 0;
    const buyInB = b.buyIn || 0;
    const canAffordA = balance.value >= buyInA;
    const canAffordB = balance.value >= buyInB;

    if (canAffordA && !canAffordB) return -1;
    if (!canAffordA && canAffordB) return 1;
    return 0;
  });

  return games.map((game: Game) => ({
    sessionId: game.gameId,
    roomCode: game.gameId,
    hostUsername: game.hostName || 'Unknown',
    currentPlayers: game.playerCount || 0,
    maxPlayers: game.maxPlayers || 4,
    buyInAmount: game.buyIn || 0,
    status: game.isActive ? 'IN_PROGRESS' : 'WAITING'
  }));
});

const connectionError = computed(() => connector?.state.error || '');
const isLoading = computed(() => !connector?.state.isConnected);

const openCreateModal = () => {
  showCreateModal.value = true;
};

const handleCreateGame = (options: { maxPlayers: number; buyIn: number; isPrivate: boolean }) => {
  if (!connector) return;
  connector.actions.createGame(options);
  showCreateModal.value = false;
};


const promptJoin = (session: { roomCode: string, buyInAmount: number }) => {
  sessionToJoin.value = {
    roomCode: session.roomCode,
    buyIn: session.buyInAmount
  };
};

const cancelJoin = () => {
  sessionToJoin.value = null;
};

const confirmJoin = () => {
  if (!sessionToJoin.value || !connector) return;
  connector.actions.joinGame(sessionToJoin.value.roomCode, currentUser.value);
  sessionToJoin.value = null;
  privateCode.value = '';
};

const handleJoinPrivate = () => {
  if (!isValidCode.value) return;
  const code = privateCode.value.toUpperCase();

  // Check if this private code corresponds to a visible session
  const existingSession = sessions.value.find(s => s.roomCode === code);

  if (existingSession) { promptJoin(existingSession); }
  else {
    // If it's a hidden/private game not in the list, show unknown buy-in
    sessionToJoin.value = {
      roomCode: code,
      buyIn: -1
    };
  }
};

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
};

const goBack = () => {
  router.push('/dashboard');
};

onMounted(async () => {
  if (connector) {
    try {
      const profile: UserProfile = await fetchFromAPI('/users/me');
      if (profile) {
        currentUser.value = profile.username;
        balance.value = parseFloat(profile.currentBalance);
      }
      connector.actions.initConnection(currentUser.value);
    } catch (error) {
      console.error("Error loading profile or connecting:", error);
      connector.actions.initConnection(currentUser.value);
    }
  }
});

onUnmounted(() => {
  if (!connector) return;
  const state = connector.state?.gameState;
  if (state === 'LANDING') connector.actions.disconnect();
});

const { currentGameId } = useSoloGameWebSocket();
watch(currentGameId, (newId) => {
  if (newId) {
    router.push(`/game/${gameTypeId}/${newId}`);
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

          <button @click="openCreateModal" class="btn-create">
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

          <button
            @click="promptJoin(session)"
            class="btn-join"
            :disabled="session.currentPlayers >= session.maxPlayers || balance < session.buyInAmount"
          >
            {{
              session.currentPlayers >= session.maxPlayers ? 'FULL' :
              balance < session.buyInAmount ? 'LOW FUNDS' : 'JOIN TABLE'
            }}
          </button>
        </div>
      </div>

    </main>

    <div v-if="sessionToJoin" class="modal-overlay" @click.self="cancelJoin">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Confirm Join</h3>
        </div>
        <div class="modal-body">
          <p>You are joining Table <span class="highlight-text">#{{ sessionToJoin.roomCode }}</span>.</p>

          <div class="cost-summary">
            <span class="cost-label">Buy-In Required:</span>
            <span class="cost-value" :class="{'unknown': sessionToJoin.buyIn === -1}">
              {{ sessionToJoin.buyIn === -1 ? 'UNKNOWN' : formatCurrency(sessionToJoin.buyIn) }}
            </span>
          </div>

          <p v-if="sessionToJoin.buyIn === -1" class="disclaimer warning">
            This is a private room. The buy-in amount is not visible. Ensure you have sufficient funds before joining.
          </p>
          <p v-else class="disclaimer">
            This amount will be deducted from your balance immediately.
          </p>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="cancelJoin">Cancel</button>
          <button class="btn-confirm" @click="confirmJoin">
            {{ sessionToJoin.buyIn === -1 ? 'Attempt Join' : 'Pay & Join' }}
          </button>
        </div>
      </div>
    </div>

    <CreateGameModal
      :is-open="showCreateModal"
      :is-loading="isLoading"
      :user-balance="balance"
      @close="showCreateModal = false"
      @create="handleCreateGame"
    />
  </div>
</template>

<style scoped>
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

/* Modal Styles */
.btn-cancel { background: #374151; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: bold; padding: 10px 20px; transition: background 0.2s; }
.btn-cancel:hover { background: #4b5563; }
.btn-confirm { background: #facc15; border: none; border-radius: 8px; color: #854d0e; cursor: pointer; font-weight: bold; padding: 10px 20px; transition: transform 0.2s; }
.btn-confirm:hover { transform: translateY(-1px); }
.cost-label { color: #9ca3af; font-size: 0.9rem; text-transform: uppercase; }
.cost-summary { align-items: center; background: #374151; border-radius: 12px; display: flex; justify-content: space-between; margin: 1.5rem 0; padding: 1rem; }
.cost-value { color: #facc15; font-family: 'Courier New', monospace; font-size: 1.4rem; font-weight: bold; }
.cost-value.unknown { color: #f87171; letter-spacing: 1px; }
.disclaimer { color: #ef4444; font-size: 0.85rem; margin-top: 0; text-align: center; }
.disclaimer.warning { color: #facc15; }
.highlight-text { color: white; font-weight: bold; }
.modal-actions { display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem; }
.modal-body { color: #d1d5db; line-height: 1.6; margin-top: 1rem; }
.modal-content { background: #1f2937; border: 1px solid #374151; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); max-width: 400px; padding: 2rem; position: relative; width: 90%; }
.modal-header h3 { color: white; font-size: 1.5rem; font-weight: bold; margin: 0; }
.modal-overlay { align-items: center; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); bottom: 0; display: flex; justify-content: center; left: 0; position: fixed; right: 0; top: 0; z-index: 1000; }

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
