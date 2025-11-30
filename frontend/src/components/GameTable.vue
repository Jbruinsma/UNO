<script setup lang="ts">
import { computed } from 'vue';
import { useGameWebSocket } from '../composables/useGameWebSocket';

const {
  players,
  playerNames,
  playerId,
  myHand,
  topCard,
  currentPlayerId,
  isMyTurn,
  playCard,
  drawCard,
  direction,
  otherPlayerCardCounts
} = useGameWebSocket();

// Filter opponents (Everyone except me)
const opponents = computed(() => players.value.filter(p => p !== playerId.value));

// --- Positioning Logic (Circular Table) ---
const getOpponentStyle = (index: number, total: number) => {
  if (total === 1) return { top: '0%', left: '50%', transform: 'translate(-50%, -50%)' };

  // Place opponents in an arc from 180deg (Left) to 360deg (Right)
  const startAngle = 180;
  const endAngle = 360;
  const range = endAngle - startAngle;
  const step = range / (total + 1);
  const angle = startAngle + (step * (index + 1));
  const rad = (angle * Math.PI) / 180;

  const radius = 42; // Distance from center (%)

  const left = 50 + (radius * Math.cos(rad));
  const top = 50 + (radius * Math.sin(rad));

  return {
    left: `${left}%`,
    top: `${top}%`,
    transform: 'translate(-50%, -50%)'
  };
};

// --- Card Helper Logic ---
const getCardStyle = (cardCode: string) => {
  if (!cardCode) return { color: 'gray', label: '?' };
  const [colorCode, val] = cardCode.split('-');

  const colors: Record<string, string> = {
    'R': '#ef4444', 'B': '#3b82f6', 'G': '#22c55e', 'Y': '#eab308', 'W': '#1f2937'
  };

  return {
    bg: colors[colorCode] || '#94a3b8',
    label: val
  };
};

const handleCardClick = (card: string) => {
  if (isMyTurn.value) playCard(card);
};
</script>

<template>
  <div class="game-container">

    <!-- CIRCULAR TABLE SURFACE -->
    <div class="table-surface">

      <!-- DIRECTION INDICATOR RING -->
      <div
        class="direction-ring"
        :class="{ 'counter-clockwise': direction === -1 }"
      >
        <svg viewBox="0 0 100 100" class="arrow-svg">
          <path id="curve" d="M 10,50 a 40,40 0 1,1 80,0 a 40,40 0 1,1 -80,0" fill="transparent" />
          <text width="500">
            <textPath xlink:href="#curve" class="arrow-text">
              ➤ &nbsp;&nbsp;&nbsp; ➤ &nbsp;&nbsp;&nbsp; ➤ &nbsp;&nbsp;&nbsp; ➤ &nbsp;&nbsp;&nbsp;
            </textPath>
          </text>
        </svg>
      </div>

      <!-- CENTER PILES -->
      <div class="center-area">

        <!-- DRAW PILE -->
        <div class="card-pile draw-pile" @click="drawCard">
          <div class="playing-card card-back">
            <span class="inner-logo">UNO</span>
          </div>
        </div>

        <!-- DISCARD PILE -->
        <div class="card-pile discard-pile">
          <div
            v-if="topCard"
            class="playing-card face-up"
            :style="{ backgroundColor: getCardStyle(topCard).bg }"
          >
            <span class="card-value">{{ getCardStyle(topCard).label }}</span>
          </div>
          <!-- Placeholder slot if empty -->
          <div v-else class="card-placeholder"></div>
        </div>

      </div>

      <!-- OPPONENTS -->
      <div
        v-for="(opId, index) in opponents"
        :key="opId"
        class="opponent-seat"
        :style="getOpponentStyle(index, opponents.length)"
      >
        <div class="opponent-content" :class="{ 'is-active': opId === currentPlayerId }">

          <div class="avatar-group">
            <div class="avatar-circle">
              {{ playerNames[opId]?.charAt(0).toUpperCase() }}
            </div>
            <span class="op-name">{{ playerNames[opId] }}</span>
          </div>

          <!-- Opponent Hand (Mini Cards) -->
          <div class="mini-hand">
            <div
              v-for="n in (otherPlayerCardCounts[opId] || 0)"
              :key="n"
              class="mini-card"
              :style="{ transform: `rotate(${(n-1) * 5}deg)` }"
            ></div>
          </div>

        </div>
      </div>

    </div>

    <!-- TURN BANNER -->
    <div class="turn-banner" :class="{ 'my-turn': isMyTurn }">
      {{ isMyTurn ? "YOUR TURN" : `${playerNames[currentPlayerId] || 'Someone'}'s Turn` }}
    </div>

    <!-- MY HAND -->
    <div class="my-hand-container">
      <div class="hand-scroll">
        <div
          v-for="(card, index) in myHand"
          :key="`${card}-${index}`"
          class="playing-card hand-card"
          :class="{ 'playable': isMyTurn }"
          :style="{ backgroundColor: getCardStyle(card).bg }"
          @click="handleCardClick(card)"
        >
          <span class="card-value">{{ getCardStyle(card).label }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.game-container {
  height: 100vh;
  width: 100vw;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Segoe UI', sans-serif;
  position: relative;
}

/* --- THE TABLE --- */
.table-surface {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70vh;
  height: 70vh;
  border-radius: 50%;
  background: radial-gradient(circle, #334155 0%, #1e293b 70%);
  box-shadow: 0 0 50px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* --- DIRECTION RING --- */
.direction-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  animation: rotate-cw 20s linear infinite;
  opacity: 0.1;
}
.direction-ring.counter-clockwise { animation: rotate-ccw 20s linear infinite; }
.arrow-svg { width: 100%; height: 100%; }
.arrow-text { font-size: 10px; fill: white; letter-spacing: 5px; }

@keyframes rotate-cw { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes rotate-ccw { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }

/* --- CENTER PILES --- */
.center-area {
  display: flex;
  gap: 30px;
  z-index: 10;
}

.card-pile {
  position: relative;
  /* Ensure container doesn't block clicks */
}

/* Shared Card Style for Hand, Draw, and Discard */
.playing-card {
  width: 100px;
  height: 140px;
  border-radius: 12px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.3);
  position: relative;
  border: 4px solid white;
  user-select: none;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Specific Draw Pile Styling */
.draw-pile .playing-card.card-back {
  background: #111827; /* Dark background */
  cursor: pointer;
  /* Layered shadow to look like a stack */
  box-shadow:
    1px 1px 0 #ef4444,
    2px 2px 0 #111827,
    3px 3px 0 #ef4444,
    4px 4px 0 #111827,
    5px 5px 0 #ef4444,
    6px 6px 10px rgba(0,0,0,0.5);
}

/* Draw Pile Hover Animation */
.draw-pile:hover .playing-card {
  transform: scale(1.05) rotate(-2deg);
  box-shadow: 0 10px 25px rgba(0,0,0,0.5); /* Lift up effect */
}

.draw-pile:active .playing-card {
  transform: scale(0.95);
}

.inner-logo {
  color: #ef4444;
  font-weight: 900;
  font-size: 1.5rem;
  transform: rotate(-5deg);
}

.card-placeholder {
  width: 100px;
  height: 140px;
  border: 2px dashed rgba(255,255,255,0.2);
  border-radius: 12px;
}

.card-value {
  color: white;
  font-size: 3rem;
  font-weight: 800;
  text-shadow: 2px 2px 0px rgba(0,0,0,0.2);
}

/* --- OPPONENTS --- */
.opponent-seat {
  position: absolute;
  width: 120px;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.opponent-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.6;
  transition: all 0.3s;
  position: relative;
}

.opponent-content.is-active {
  opacity: 1;
  transform: scale(1.15);
}

.opponent-content.is-active .avatar-circle {
  box-shadow: 0 0 15px #facc15, 0 0 30px rgba(250, 204, 21, 0.4);
  border-color: #facc15;
}

.avatar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 5;
  background: rgba(15, 23, 42, 0.8);
  padding: 5px;
  border-radius: 12px;
}

.avatar-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #475569;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  border: 3px solid #334155;
  margin-bottom: 5px;
}

.op-name {
  font-size: 0.85rem;
  color: white;
  font-weight: 600;
}

.mini-hand {
  display: flex;
  position: absolute;
  top: 10px;
  left: 60px;
  height: 40px;
}

.mini-card {
  width: 20px;
  height: 30px;
  background: #64748b;
  border: 1px solid #94a3b8;
  border-radius: 3px;
  margin-left: -12px;
  transform-origin: bottom center;
}

/* --- TURN BANNER --- */
.turn-banner {
  position: absolute;
  bottom: 220px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 24px;
  border-radius: 20px;
  background: rgba(0,0,0,0.5);
  color: #94a3b8;
  font-weight: bold;
  font-size: 1rem;
  backdrop-filter: blur(4px);
  pointer-events: none;
  transition: all 0.3s;
}

.turn-banner.my-turn {
  background: #22c55e;
  color: white;
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
  transform: translateX(-50%) scale(1.1);
}

/* --- MY HAND --- */
.my-hand-container {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 200px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: linear-gradient(to top, rgba(15,23,42,1) 0%, rgba(15,23,42,0) 100%);
  padding-bottom: 20px;
}

.hand-scroll {
  display: flex;
  padding: 0 40px;
  margin-left: 20px;
}

.hand-card {
  margin-right: -50px;
  /* Uses .playing-card style automatically */
}

.hand-card:last-child { margin-right: 0; }

.hand-card:hover {
  transform: translateY(-40px) scale(1.1) rotate(2deg);
  z-index: 50;
  margin-right: 0px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.5);
}

.hand-card.playable { cursor: pointer; }

@media (max-width: 600px) {
  .table-surface { width: 90vw; height: 90vw; top: 40%; }
  .playing-card { width: 80px; height: 120px; }
  .card-placeholder { width: 80px; height: 120px; }
}
</style>
