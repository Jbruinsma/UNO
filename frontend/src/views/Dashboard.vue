<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { fetchFromAPI } from "@/utils/api.ts";

const router = useRouter();

const username = ref<string>('');
const balance = ref<number>(0.00);
const showUserMenu = ref(false);
const isLoading = ref(true);
const isAdmin = ref(false);

interface Game {
  gameTypeId: string;
  displayName: string;
  description: string;
  playerCount: number;
  status: 'ACTIVE' | 'MAINTENANCE' | 'COMING_SOON';
  imageAsset: string;
  frontendRoute: string;
}

interface UserProfile {
  userId: string;
  username: string;
  email: string;
  birthday: string;
  currentBalance: number;
  createdAt: string;
}

const games = ref<Game[]>([]);

onMounted(async () => {
  // 2. Check Local Storage on mount
  const role = localStorage.getItem('user_role');
  isAdmin.value = role === 'ADMIN';

  const token = localStorage.getItem('token');
  if (!token) {
    await router.push('/login');
    return;
  }

  try {
    const [catalogData, userData] = await Promise.all([
      fetchFromAPI<Game[]>('/dashboard/catalog'),
      fetchFromAPI<UserProfile>('/users/me')
    ]);

    games.value = catalogData
      .sort((a: any, b: any) => {
        if (a.status === 'ACTIVE') return -1;
        if (b.status === 'ACTIVE') return 1;
        return 0;
      })
      .map((game: any) => ({
        ...game,
        playerCount: game.gameTypeId === 'solo' ? 124 : 0
      }));

    username.value = userData.username;
    balance.value = userData.currentBalance;

  } catch (e) {
    console.error("Failed to load dashboard data", e);
    localStorage.removeItem('token');
    await router.push('/login');
    return;
  } finally {
    isLoading.value = false;
  }
});

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user_id');
  localStorage.removeItem('user_role');
  router.push('/login');
};

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
};

const playGame = (game: Game) => {
  if (game.status !== 'ACTIVE') return;
  router.push(game.frontendRoute);
};
</script>

<template>
  <div class="dashboard-container">

    <header class="navbar">
      <div class="nav-left">
        <h1 class="brand">ANTE <span class="badge">ONLINE</span></h1>
      </div>

      <div class="nav-right">
        <div class="balance-pill">
          <span class="currency-symbol">$</span>
          <span class="amount">{{ formatCurrency(balance).replace('$', '') }}</span>
          <button class="add-funds-btn">+</button>
        </div>

        <div class="user-menu-container" @click="showUserMenu = !showUserMenu">
          <div class="avatar">
            {{ username.charAt(0).toUpperCase() }}
          </div>
          <span class="username">{{ username }}</span>
          <span class="chevron">▼</span>

          <div v-if="showUserMenu" class="dropdown">
            <a v-if="isAdmin" href="#" class="dropdown-item">Admin</a>

            <a href="#" class="dropdown-item">Settings</a>
            <a href="#" class="dropdown-item">Transaction History</a>
            <div class="divider"></div>
            <button @click="handleLogout" class="dropdown-item logout">Sign Out</button>
          </div>
        </div>
      </div>
    </header>

    <main class="main-content">

      <div class="hero-section">
        <h2>What would you like to play?</h2>
        <p>Select a game table to join the action.</p>
      </div>

      <div v-if="isLoading" class="loading-container">
        <p>Loading tables...</p>
      </div>

      <div v-else class="games-grid">
        <div
          v-for="game in games"
          :key="game.gameTypeId"
          class="game-card"
          :class="{ 'disabled': game.status !== 'ACTIVE' }"
        >
          <div class="card-header">
            <span class="game-icon">{{ game.imageAsset }}</span>

            <span v-if="game.status === 'ACTIVE'" class="live-indicator">
              <span class="dot"></span> {{ game.playerCount }} Playing
            </span>
            <span v-else class="status-badge">{{ game.status.replace('_', ' ') }}</span>
          </div>

          <div class="card-body">
            <h3>{{ game.displayName }}</h3>
            <p>{{ game.description }}</p>
          </div>

          <div class="card-footer">
            <button
              class="btn-play"
              @click="playGame(game)"
              :disabled="game.status !== 'ACTIVE'"
            >
              {{ game.status === 'ACTIVE' ? 'Play Now' : 'Coming Soon' }}
            </button>
          </div>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
.loading-container {
  text-align: center;
  color: #9ca3af;
  margin-top: 50px;
  font-size: 1.2rem;
}

.dashboard-container {
  background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
  min-height: 100vh;
  color: #fff;
  font-family: 'Segoe UI', sans-serif;
  display: flex;
  flex-direction: column;
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

.brand {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -1px;
  color: #fff;
  margin: 0;
}

.badge {
  background: #facc15;
  color: #854d0e;
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 12px;
  vertical-align: middle;
  margin-left: 5px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.balance-pill {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 20px;
  padding: 4px 4px 4px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: bold;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

.amount {
  color: #facc15;
  font-family: 'Courier New', monospace;
  font-size: 1.1rem;
}

.add-funds-btn {
  background: #facc15;
  color: #854d0e;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.add-funds-btn:hover {
  transform: scale(1.1);
}

.user-menu-container {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  position: relative;
  user-select: none;
}

.avatar {
  width: 35px;
  height: 35px;
  background: linear-gradient(135deg, #6366f1, #a855f7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border: 2px solid rgba(255,255,255,0.2);
}

.username {
  font-weight: 600;
}

.chevron {
  font-size: 0.7rem;
  opacity: 0.7;
}

.dropdown {
  position: absolute;
  top: 120%;
  right: 0;
  background: white;
  color: #1f2937;
  border-radius: 12px;
  width: 180px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.5);
  overflow: hidden;
  animation: slideDown 0.2s ease;
}

.dropdown-item {
  display: block;
  padding: 12px 16px;
  text-decoration: none;
  color: #374151;
  font-size: 0.9rem;
  transition: background 0.2s;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item.logout {
  color: #dc2626;
}

.divider {
  height: 1px;
  background: #e5e7eb;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 3rem 2rem;
  flex: 1;
}

.hero-section {
  margin-bottom: 2rem;
}

.hero-section h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.hero-section p {
  color: #9ca3af;
  font-size: 1.1rem;
}

.games-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}

.game-card {
  background: white;
  border-radius: 20px;
  padding: 1.5rem;
  color: #1f2937;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  height: 250px;
  position: relative;
  overflow: hidden;
}

.game-card:hover:not(.disabled) {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}

.game-card.disabled {
  opacity: 0.7;
  background: #e5e7eb;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.game-icon {
  font-size: 2.5rem;
}

.live-indicator {
  font-size: 0.8rem;
  color: #059669;
  font-weight: 700;
  background: #d1fae5;
  padding: 4px 8px;
  border-radius: 10px;
}

.dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #059669;
  border-radius: 50%;
  margin-right: 4px;
  animation: pulse 2s infinite;
}

.status-badge {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: bold;
  background: #9ca3af;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
}

.card-body h3 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
  font-weight: 800;
}

.card-body p {
  color: #6b7280;
  font-size: 0.95rem;
  line-height: 1.4;
}

.card-footer {
  margin-top: auto;
}

.btn-play {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: none;
  background: #1f2937;
  color: white;
  font-weight: bold;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-play:hover {
  background: #374151;
}

.btn-play:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 600px) {
  .navbar { padding: 1rem; }
  .nav-right { gap: 10px; }
  .balance-pill { padding-left: 10px; }
  .amount { font-size: 0.9rem; }
  .username { display: none; }
}
</style>
