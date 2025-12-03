<script setup lang="ts">
import { computed, watch, ref, onMounted } from 'vue';
import { useGameWebSocket } from '../composables/useGameWebSocket';

const {
  gameState,
  leaveGame,
  players,
  playerNames,
  playerId,
  myHand,
  currentActiveColor,
  topCard,
  currentPlayerId,
  isMyTurn,
  playCard,
  drawCard,
  changeColorWithWild,
  changeColorWithWildAndDraw4,
  direction,
  otherPlayerCardCounts,
  event,
  endGame,
  backToLobby,
  isConnected
} = useGameWebSocket();

// --- Local State ---
const showReverseAnimation = ref(false);
const showColorPicker = ref(false);
const wildCardIsDraw4 = ref<boolean>(false);
const skippedPlayerId = ref<string | null>(null);
const discardPileBump = ref(false);
const isInteractionLocked = ref(false);

// --- Win/Game Over State ---
const showWinnerAnimation = ref(false);
const showGameOverModal = ref(false);
const winnerName = ref('');

// Animation State
interface FlyingCard {
  id: number;
  style: any;
  cardCode?: string;
}
const flyingCards = ref<FlyingCard[]>([]);
let nextFlyingId = 0;

// Filter opponents (Everyone except me)
const opponents = computed(() => players.value.filter(p => p !== playerId.value));

// --- Positioning Logic ---
const getOpponentCoords = (index: number, total: number) => {
  if (total === 1) return { top: 0, left: 50 };

  const startAngle = 135;
  const endAngle = 405;
  const range = endAngle - startAngle;
  const step = range / (total + 1);
  const angle = startAngle + (step * (index + 1));
  const rad = (angle * Math.PI) / 180;
  const radius = 53;
  const left = 50 + (radius * Math.cos(rad));
  const top = 50 + (radius * Math.sin(rad));

  return { left, top };
};

const getOpponentStyle = (index: number, total: number) => {
  const { left, top } = getOpponentCoords(index, total);
  return {
    left: `${left}%`,
    top: `${top}%`,
    transform: 'translate(-50%, -50%)'
  };
};

// --- SMART TURN ARROW LOGIC ---
const currentRotation = ref(0); // Persistent rotation value
const tempArrowTargetId = ref<string | null>(null); // For animations (like pointing at skipped player)

// Helper to get the target static angle for any player ID
const getAngleForPlayer = (targetId: string) => {
  if (targetId === playerId.value) return 0; // My angle

  const totalOpponents = opponents.value.length;
  const index = opponents.value.indexOf(targetId);

  if (index === -1) return 0; // Fallback

  if (totalOpponents === 1) return 180;

  const startAngle = 135;
  const startRange = 135; // We use startAngle logic from positioning
  const endAngle = 405;
  const range = endAngle - startRange;
  const step = range / (totalOpponents + 1);
  const angle = startAngle + (step * (index + 1));

  return angle - 90; // Adjust for arrow orientation
};

// Watch for turn changes OR temp target overrides (Skip animation)
watch([currentPlayerId, tempArrowTargetId], ([newCurrent, newTemp]) => {
  const targetId = newTemp || newCurrent;

  if (!targetId) return;

  const targetAngle = getAngleForPlayer(targetId);
  const currentNormalized = currentRotation.value % 360;
  let diff = targetAngle - currentNormalized;

  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;

  const gameDir = direction.value;

  if (gameDir === 1 && diff < 0) {
    diff += 360;
  } else if (gameDir === -1 && diff > 0) {
    diff -= 360;
  }

  currentRotation.value += diff;
});

// Initialize rotation on mount
onMounted(() => {
  if (currentPlayerId.value) {
    currentRotation.value = getAngleForPlayer(currentPlayerId.value);
  }
});

// --- Card Style Logic ---
const getCardMeta = (cardCode: string) => {
  if (!cardCode) return { bg: '#cbd5e1', label: '?', isWild: false, color: '#64748b' };

  const [colorCode, val] = cardCode.split('-');
  const colors: Record<string, string> = {
    'R': '#ef4444', 'B': '#3b82f6', 'G': '#22c55e', 'Y': '#eab308', 'W': '#0f172a'
  };

  let label = val;
  let isWild = false;

  if (val === 'S') label = '⊘';
  else if (val === 'R') label = '⇄';
  else if (val === 'D2') label = '+2';
  else if (val === 'Wild') { label = '★'; isWild = true; }
  else if (val === 'W4') { label = '+4'; isWild = true; }

  return {
    bg: colors[colorCode] || '#94a3b8',
    label: label,
    isWild: isWild,
    color: 'white'
  };
};

const getActiveColorHex = computed(() => {
  switch (currentActiveColor.value) {
    case 'R': return '#ef4444';
    case 'B': return '#3b82f6';
    case 'G': return '#22c55e';
    case 'Y': return '#eab308';
    default: return 'transparent';
  }
});

// --- Game Logic ---
const isCardPlayable = (card: string) => {
  if (!topCard.value) return false;
  const [cColor, cValue] = card.split('-');
  const [tColor, tValue] = topCard.value.split('-');

  if (cColor === 'W') return true;
  const targetColor = currentActiveColor.value || tColor;
  if (cColor === targetColor) return true;
  return cValue === tValue;
};

// --- Handlers ---
const handleCardClick = (card: string) => {
  if (isMyTurn.value && isCardPlayable(card) && !isInteractionLocked.value && isConnected.value) {
    isInteractionLocked.value = true;
    triggerSelfPlayAnimation(card);
    playCard(card);
    setTimeout(() => { isInteractionLocked.value = false }, 1000);
  }
};

const handleDrawClick = () => {
  if (isMyTurn.value && !isInteractionLocked.value && isConnected.value) {
    isInteractionLocked.value = true;
    drawCard();
    setTimeout(() => { isInteractionLocked.value = false; }, 1000);
  }
};

const handleColorSelect = (color: string) => {
  if (wildCardIsDraw4.value) { changeColorWithWildAndDraw4(color) }
  else { changeColorWithWild(color); }
  showColorPicker.value = false;
  wildCardIsDraw4.value = false;
};

const handleBackToLobby = () => {
  backToLobby();
  gameState.value = 'LOBBY';
};

const handleLeave = () => {
  leaveGame();
};

// --- ANIMATION CONTROLLER ---
const triggerPileImpact = () => {
  setTimeout(() => {
    discardPileBump.value = true;
    setTimeout(() => { discardPileBump.value = false; }, 200);
  }, 600);
};

const createFlyingCard = (start: any, end: any, delay: number = 0, cardCode?: string) => {
  setTimeout(() => {
    const id = nextFlyingId++;
    flyingCards.value.push({
      id,
      style: { ...start, transition: 'none' },
      cardCode
    });

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const card = flyingCards.value.find(c => c.id === id);
        if (card) {
          card.style = {
            ...end,
            transition: 'all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1)'
          };
        }
      });
    });

    setTimeout(() => {
      flyingCards.value = flyingCards.value.filter(c => c.id !== id);
    }, 700 + delay);
  }, delay);
};

const triggerDrawAnimation = (targetPlayerId: string, count: number) => {
  let endStyle: any;

  if (targetPlayerId === playerId.value) {
    endStyle = {
      top: '90%', left: '50%', opacity: 0,
      transform: `translate(-50%, -50%) scale(1) rotate(${Math.random() * 20 - 10}deg)`
    };
  } else {
    const index = opponents.value.indexOf(targetPlayerId);
    if (index === -1) return;
    const { left, top } = getOpponentCoords(index, opponents.value.length);
    endStyle = {
      top: `${top}%`, left: `${left}%`, opacity: 0,
      transform: 'translate(-50%, -50%) scale(0.5) rotate(0deg)'
    };
  }

  for (let i = 0; i < count; i++) {
    createFlyingCard(
      {
        top: '45%', left: '50%', opacity: 1,
        transform: 'translate(-50%, -50%) scale(0.5) rotate(0deg)'
      },
      endStyle,
      i * 250
    );
  }
};

const triggerOpponentPlayAnimation = (playerId: string) => {
  const index = opponents.value.indexOf(playerId);
  if (index === -1) return;
  const { left, top } = getOpponentCoords(index, opponents.value.length);

  createFlyingCard(
    {
      top: `${top}%`, left: `${left}%`, opacity: 1,
      transform: 'translate(-50%, -50%) scale(0.5) rotate(0deg)'
    },
    {
      top: '50%', left: '50%', opacity: 0,
      transform: 'translate(-50%, -50%) scale(1) rotate(0deg)'
    },
  );
  triggerPileImpact();
};

const triggerSelfPlayAnimation = (cardCode: string) => {
  createFlyingCard(
    {
      top: '85%', left: '50%', opacity: 1,
      transform: 'translate(-50%, -50%) scale(1.1) rotate(0deg)',
      zIndex: 100
    },
    {
      top: '50%', left: '50%', opacity: 0,
      transform: 'translate(-50%, -50%) scale(1) rotate(0deg)'
    },
    0,
    cardCode
  );
  triggerPileImpact();
};

// --- Event Watcher ---
watch(event, (newEvent) => {
  const eventType = newEvent.type;
  const originPlayerId = newEvent.player_id;
  const affectedPlayerId = newEvent.affected_player_id;

  if (eventType === 'play_card') {
    if (originPlayerId !== playerId.value) {
      triggerOpponentPlayAnimation(originPlayerId);
    }
  } else if (eventType === 'reverse') {
    showReverseAnimation.value = true;
    setTimeout(() => { showReverseAnimation.value = false; }, 2000);

  } else if (eventType === 'skip') {
    if (affectedPlayerId) {
      // 1. Force arrow to point at the victim (Detour)
      tempArrowTargetId.value = affectedPlayerId;

      // 2. Show the Skip Icon
      skippedPlayerId.value = affectedPlayerId;

      // 3. Lock interaction if it's me
      if (affectedPlayerId === playerId.value) {
         isInteractionLocked.value = true;
      }

      // 4. Release after Reduced Delay (1.2s instead of 2.0s)
      setTimeout(() => {
        tempArrowTargetId.value = null;
        skippedPlayerId.value = null;

        if (affectedPlayerId === playerId.value) {
          isInteractionLocked.value = false;
        }
      }, 1200);
    }

  } else if (eventType === 'wild_color_pick') {
    if (playerId.value === originPlayerId) { showColorPicker.value = true; }

  } else if (eventType === 'wild_color_pick_draw4') {
    if (playerId.value === originPlayerId) {
      showColorPicker.value = true;
      wildCardIsDraw4.value = true;
    }

  } else if (eventType === 'draw4' || eventType === 'draw2') {
    const count: number = eventType === 'draw4' ? 4 : 2;
    triggerDrawAnimation(affectedPlayerId, count);
    if (affectedPlayerId === playerId.value) {
      isInteractionLocked.value = true;
      const totalAnimTime = (count * 250) + 700;
      setTimeout(() => { isInteractionLocked.value = false; }, totalAnimTime);
    }

  } else if (eventType === 'draw_card') {
    triggerDrawAnimation(originPlayerId, 1);

  } else if (eventType === 'win') {
    triggerWin(playerNames.value[originPlayerId] || 'Player');
  }
});

watch(() => players.value.length, async (newCount) => {

  if (newCount <= 1) {
    await triggerWin(playerNames.value[playerId.value]);
    return
  }

});

async function triggerWin(winningPlayerName: string){
  winnerName.value = winningPlayerName;
  showWinnerAnimation.value = true;
  endGame()
  setTimeout(() => {
      showWinnerAnimation.value = false;
      showGameOverModal.value = true;
    }, 3000);
}

</script>

<template>
  <div class="game-container">

    <div v-if="!isConnected" class="connection-warning">
      Trying to reconnect...
    </div>

    <div v-if="showWinnerAnimation" class="winner-overlay">
      <div class="crown-icon">👑</div>
      <div class="winner-text">{{ winnerName }} WINS!</div>
    </div>

    <div v-if="showGameOverModal" class="modal-backdrop">
      <div class="modal-content">
        <div class="modal-crown">👑</div>
        <h2 class="modal-title">GAME OVER</h2>
        <p class="modal-subtitle">{{ winnerName }} takes the victory!</p>
        <div class="modal-actions">
          <button class="action-btn primary" @click="handleBackToLobby">Back to Lobby</button>
          <button class="action-btn secondary" @click="handleLeave">Leave Game</button>
        </div>
      </div>
    </div>

    <div v-if="showReverseAnimation" class="reverse-overlay">
      <div class="reverse-icon">⇄</div>
      <div class="reverse-text">REVERSED!</div>
    </div>

    <div class="flying-card-layer">
      <div
        v-for="card in flyingCards"
        :key="card.id"
        class="flying-card-visual"
        :style="card.style"
      >
        <div
          v-if="card.cardCode"
          class="playing-card face-up"
          :style="{ backgroundColor: getCardMeta(card.cardCode).bg }"
        >
          <div v-if="getCardMeta(card.cardCode).isWild" class="wild-bg"></div>
          <span class="corner-label top-left">{{ getCardMeta(card.cardCode).label }}</span>
          <span class="corner-label bottom-right">{{ getCardMeta(card.cardCode).label }}</span>
          <span class="card-value">{{ getCardMeta(card.cardCode).label }}</span>
        </div>

        <div v-else class="playing-card card-back">
          <span class="inner-logo">UNO</span>
        </div>
      </div>
    </div>

    <div v-if="showColorPicker" class="picker-backdrop">
      <div class="picker-modal">
        <h2 class="picker-title">CHOOSE A COLOR</h2>
        <div class="color-grid">
          <button class="color-btn red" @click="handleColorSelect('R')"></button>
          <button class="color-btn blue" @click="handleColorSelect('B')"></button>
          <button class="color-btn green" @click="handleColorSelect('G')"></button>
          <button class="color-btn yellow" @click="handleColorSelect('Y')"></button>
        </div>
      </div>
    </div>

    <div class="table-surface">

      <div
        class="turn-dial-track"
        :class="{ 'is-my-turn-track': isMyTurn }"
        :style="{ transform: `translate(-50%, -50%) rotate(${currentRotation}deg)` }"
      >
        <div class="turn-arrow-container">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="turn-arrow-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25 12 21m0 0-3.75-3.75M12 21V3" />
          </svg>
        </div>
      </div>

      <div class="direction-ring" :class="{ 'counter-clockwise': direction === -1 }">
        <svg viewBox="0 0 100 100" class="arrow-svg">
          <defs>
            <symbol id="icon-left" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 15.75 3 12m0 0 3.75-3.75M3 12h18" />
            </symbol>
            <symbol id="icon-right" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
            </symbol>
          </defs>
          <g v-for="i in 4" :key="i" :transform="`rotate(${(i - 1) * 90}, 50, 50)`">
            <use :href="direction === 1 ? '#icon-right' : '#icon-left'" x="46" y="6" width="8" height="8" />
          </g>
        </svg>
      </div>

      <div class="center-area">

        <div
          class="card-pile draw-pile"
          :class="{ 'disabled-pile': !isMyTurn || isInteractionLocked || !isConnected }"
          @click="handleDrawClick"
        >
          <div class="playing-card card-back">
            <span class="inner-logo">UNO</span>
          </div>
        </div>

        <div
          class="card-pile discard-pile"
          :class="{ 'bump-effect': discardPileBump }"
        >
          <div
             class="active-color-glow"
             :style="{ borderColor: getActiveColorHex, boxShadow: `0 0 30px ${getActiveColorHex}` }"
          ></div>

          <div
            v-if="topCard"
            class="playing-card face-up"
            :style="{ backgroundColor: getCardMeta(topCard).bg }"
          >
            <div v-if="getCardMeta(topCard).isWild" class="wild-bg"></div>
            <span class="corner-label top-left">{{ getCardMeta(topCard).label }}</span>
            <span class="corner-label bottom-right">{{ getCardMeta(topCard).label }}</span>
            <span class="card-value">{{ getCardMeta(topCard).label }}</span>
          </div>
          <div v-else class="card-placeholder"></div>
        </div>

      </div>

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
              <div v-if="skippedPlayerId === opId" class="skip-badge">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="skip-icon">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
            </div>
            <span class="op-name">{{ playerNames[opId] }}</span>
          </div>

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

    <Transition name="fade">
      <div v-if="skippedPlayerId === playerId" class="self-skip-alert">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="skip-icon-large">
          <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
        <span>SKIPPED!</span>
      </div>
    </Transition>

    <div class="my-hand-container">
      <div class="hand-scroll">
        <div
          v-for="(card, index) in myHand"
          :key="`${card}-${index}`"
          class="playing-card hand-card"
          :class="{
            'playable': isMyTurn && isCardPlayable(card) && !isInteractionLocked && isConnected,
            'unplayable': !(isMyTurn && isCardPlayable(card) && !isInteractionLocked && isConnected)
          }"
          :style="{ backgroundColor: getCardMeta(card).bg }"
          @click="handleCardClick(card)"
        >
          <div v-if="getCardMeta(card).isWild" class="wild-bg"></div>
          <span class="corner-label top-left">{{ getCardMeta(card).label }}</span>
          <span class="corner-label bottom-right">{{ getCardMeta(card).label }}</span>
          <span class="card-value">{{ getCardMeta(card).label }}</span>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.bump-effect { animation: bump 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
@keyframes bump { 0% { transform: scale(1); } 50% { transform: scale(0.9); } 100% { transform: scale(1); } }

/* --- REVISED TURN DIAL STYLES --- */
.turn-dial-track {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 440px; /* Increased Orbit Diameter to clear cards */
  height: 440px;
  pointer-events: none;
  z-index: 1; /* Below cards (cards are z-index 10 in center-area) */
  border: 2px dashed rgba(255, 255, 255, 0.1); /* Visible Track */
  border-radius: 50%;
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.3s;
}

/* Container to position the arrow on the edge of the circle */
.turn-arrow-container {
  position: absolute;
  bottom: -15px; /* Sits on the bottom edge */
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.turn-arrow-svg {
  width: 50px; /* Bolder size */
  height: 50px;
  color: #64748b; /* Inactive color */
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.5));
  transition: all 0.3s ease;
}

/* My Turn State: Green, Pulse, Larger */
.turn-dial-track.is-my-turn-track {
  border-color: rgba(34, 197, 94, 0.3); /* Track glows slightly */
  animation: pulse-ring 2s infinite;
}

.turn-dial-track.is-my-turn-track .turn-arrow-svg {
  color: #22c55e;
  transform: scale(1.4); /* Bigger */
  filter: drop-shadow(0 0 15px #22c55e);
}

@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
  70% { box-shadow: 0 0 0 20px rgba(34, 197, 94, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.action-btn { border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: bold; padding: 12px 24px; transition: transform 0.1s; width: 100%; }
.action-btn:active { transform: scale(0.95); }
.action-btn.primary { background: #22c55e; color: white; margin-bottom: 10px; }
.action-btn.secondary { background: #475569; color: white; }
.active-color-glow { border: 2px solid transparent; border-radius: 16px; height: 150px; left: 50%; pointer-events: none; position: absolute; top: 50%; transform: translate(-50%, -50%); transition: all 0.5s ease; width: 110px; z-index: 0; }
.arrow-svg { fill: none; height: 100%; stroke: white; stroke-width: 2; width: 100%; }
.avatar-circle { align-items: center; background: #475569; border: 3px solid #334155; border-radius: 50%; color: white; display: flex; font-size: 1.2rem; font-weight: bold; height: 50px; justify-content: center; margin-bottom: 5px; position: relative; width: 50px; }
.avatar-group { align-items: center; background: rgba(15, 23, 42, 0.8); border-radius: 12px; display: flex; flex-direction: column; padding: 5px; z-index: 5; }
.blue { background-color: #3b82f6; color: #3b82f6; }
.bottom-right { bottom: 6px; right: 8px; transform: rotate(180deg); }
.card-pile { position: relative; transition: transform 0.1s; }
.card-placeholder { border: 2px dashed rgba(255,255,255,0.2); border-radius: 12px; height: 140px; width: 100px; }
.card-value { color: white; font-size: 3rem; font-weight: 800; text-shadow: 2px 2px 0px rgba(0,0,0,0.2); z-index: 2; }
.center-area { display: flex; gap: 30px; z-index: 10; }
.color-btn { border: none; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); cursor: pointer; height: 80px; transition: transform 0.1s, filter 0.1s; width: 80px; }
.color-btn:active { transform: scale(0.95); }
.color-btn:hover { filter: brightness(1.2); transform: scale(1.05); }
.color-grid { display: grid; gap: 15px; grid-template-columns: 1fr 1fr; margin-top: 25px; }
.connection-warning { background: #facc15; color: #854d0e; font-weight: bold; padding: 10px; position: fixed; text-align: center; top: 0; width: 100%; z-index: 2000; }
.corner-label { color: white; font-size: 0.9rem; font-weight: 800; position: absolute; text-shadow: 1px 1px 0 rgba(0,0,0,0.3); z-index: 2; }
.crown-icon { animation: bounce 1s infinite; font-size: 8rem; margin-bottom: 20px; }
.direction-ring { animation: rotate-cw 20s linear infinite; height: 100%; opacity: 0.15; pointer-events: none; position: absolute; width: 100%; }
.direction-ring.counter-clockwise { animation: rotate-ccw 20s linear infinite; }
.draw-pile.disabled-pile { cursor: not-allowed; filter: grayscale(1); opacity: 0.5; }
.draw-pile .playing-card.card-back { background: #111827; box-shadow: 1px 1px 0 #ef4444, 2px 2px 0 #111827, 3px 3px 0 #ef4444, 4px 4px 0 #111827, 5px 5px 0 #ef4444, 6px 6px 10px rgba(0,0,0,0.5); cursor: pointer; }
.draw-pile:active .playing-card { transform: scale(0.95); }
.draw-pile:hover .playing-card { box-shadow: 0 10px 25px rgba(0,0,0,0.5); transform: scale(1.05) rotate(-2deg); }
.disabled-pile:hover .playing-card { transform: none; box-shadow: 1px 1px 0 #ef4444, 2px 2px 0 #111827, 3px 3px 0 #ef4444, 4px 4px 0 #111827, 5px 5px 0 #ef4444, 6px 6px 10px rgba(0,0,0,0.5); }
.flying-card-layer { height: 100vh; left: 0; pointer-events: none; position: fixed; top: 0; width: 100vw; z-index: 500; }
.flying-card-visual { height: 140px; position: absolute; width: 100px; }
.game-container { background: #0f172a; display: flex; flex-direction: column; font-family: 'Segoe UI', sans-serif; height: 100vh; overflow: hidden; position: relative; width: 100vw; }
.green { background-color: #22c55e; color: #22c55e; }
.hand-card { margin-right: -50px; }
.hand-card.playable { cursor: pointer; }
.hand-card.playable:hover { box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin-right: 0px; transform: translateY(-40px) scale(1.1) rotate(2deg); z-index: 50; }
.hand-card.unplayable { cursor: not-allowed; filter: grayscale(0.8) brightness(0.7); opacity: 0.8; transform: scale(0.95); pointer-events: none; }
.hand-card:last-child { margin-right: 0; }
.hand-scroll { display: flex; margin-left: 20px; padding: 0 40px; }
.inner-logo { color: #ef4444; font-size: 1.5rem; font-weight: 900; transform: rotate(-5deg); z-index: 5; }
.mini-card { background: #64748b; border: 1px solid #94a3b8; border-radius: 3px; height: 30px; margin-left: -12px; transform-origin: bottom center; width: 20px; }
.mini-hand { display: flex; height: 40px; left: 60px; position: absolute; top: 10px; }
.modal-actions { display: flex; flex-direction: column; gap: 10px; margin-top: 30px; width: 100%; }
.modal-backdrop { align-items: center; background: rgba(0,0,0,0.8); bottom: 0; display: flex; justify-content: center; left: 0; position: fixed; right: 0; top: 0; z-index: 1000; }
.modal-content { align-items: center; background: #1e293b; border: 2px solid #facc15; border-radius: 20px; box-shadow: 0 0 50px rgba(250, 204, 21, 0.2); display: flex; flex-direction: column; max-width: 400px; padding: 40px; text-align: center; width: 90%; }
.modal-crown { font-size: 3rem; margin-bottom: 10px; }
.modal-subtitle { color: #94a3b8; font-size: 1.2rem; margin: 0; }
.modal-title { color: #facc15; font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; margin: 0 0 10px 0; text-transform: uppercase; }
.my-hand-container { align-items: flex-end; background: linear-gradient(to top, rgba(15,23,42,1) 0%, rgba(15,23,42,0) 100%); bottom: 0; display: flex; height: 200px; justify-content: center; left: 0; padding-bottom: 20px; position: absolute; width: 100%; }
.op-name { color: white; font-size: 0.85rem; font-weight: 600; }
.opponent-content { align-items: center; display: flex; flex-direction: column; opacity: 0.6; position: relative; transition: all 0.3s; }
.opponent-content.is-active { opacity: 1; transform: scale(1.15); }
.opponent-content.is-active .avatar-circle { border-color: #facc15; box-shadow: 0 0 15px #facc15, 0 0 30px rgba(250, 204, 21, 0.4); }
.opponent-seat { align-items: center; display: flex; height: 120px; justify-content: center; position: absolute; width: 120px; }
.picker-backdrop { align-items: center; backdrop-filter: blur(5px); background: rgba(0, 0, 0, 0.6); bottom: 0; display: flex; justify-content: center; left: 0; position: fixed; right: 0; top: 0; z-index: 300; }
.picker-modal { align-items: center; background: #1e293b; border: 1px solid #334155; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); display: flex; flex-direction: column; padding: 30px 50px; }
.picker-title { color: white; font-size: 1.2rem; font-weight: 800; letter-spacing: 2px; margin: 0; text-transform: uppercase; }
.playing-card { align-items: center; background: white; border: 4px solid white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); display: flex; height: 140px; justify-content: center; overflow: hidden; position: relative; transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); user-select: none; width: 100px; z-index: 1; }
.red { background-color: #ef4444; color: #ef4444; }
.reverse-icon { font-size: 6rem; line-height: 1; }
.reverse-overlay { align-items: center; animation: pop-spin 2s ease-in-out forwards; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); border-radius: 30px; color: #facc15; display: flex; flex-direction: column; height: 250px; justify-content: center; left: 50%; pointer-events: none; position: absolute; top: 50%; transform: translate(-50%, -50%); width: 300px; z-index: 200; }
.reverse-text { font-size: 2rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; }
.self-skip-alert { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 10px; color: #ef4444; z-index: 500; font-weight: 900; font-size: 2rem; text-shadow: 0 4px 10px rgba(0,0,0,0.5); animation: bounce-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); pointer-events: none; }
.skip-badge { position: absolute; top: -5px; right: -5px; background: #ef4444; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.3); animation: bounce-in 0.3s ease-out; border: 2px solid #1e293b; }
.skip-icon { width: 16px; height: 16px; stroke-width: 3; }
.skip-icon-large { width: 64px; height: 64px; stroke-width: 2.5; }
.table-surface { align-items: center; background: radial-gradient(circle, #334155 0%, #1e293b 70%); border-radius: 50%; box-shadow: 0 0 50px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.2); display: flex; height: 70vh; justify-content: center; left: 50%; position: absolute; top: 45%; transform: translate(-50%, -50%); width: 70vh; }
.top-left { left: 8px; top: 6px; }
.wild-bg { background: conic-gradient(#ef4444 0deg 90deg, #3b82f6 90deg 180deg, #eab308 180deg 270deg, #22c55e 270deg 360deg); border-radius: 50%; filter: blur(8px); height: 80px; opacity: 0.8; position: absolute; width: 80px; z-index: 1; }
.winner-overlay { align-items: center; animation: zoom-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); background: rgba(0,0,0,0.8); bottom: 0; color: #facc15; display: flex; flex-direction: column; justify-content: center; left: 0; position: fixed; right: 0; top: 0; z-index: 1000; }
.winner-text { font-size: 4rem; font-weight: 900; letter-spacing: 4px; text-shadow: 0 0 20px rgba(250, 204, 21, 0.5); text-transform: uppercase; }
.yellow { background-color: #eab308; color: #eab308; }

@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
@keyframes pop-spin { 0% { opacity: 0; transform: translate(-50%, -50%) scale(0) rotate(-90deg); } 20% { opacity: 1; transform: translate(-50%, -50%) scale(1.1) rotate(0deg); } 80% { opacity: 1; transform: translate(-50%, -50%) scale(1) rotate(0deg); } 100% { opacity: 0; transform: translate(-50%, -50%) scale(0) rotate(90deg); } }
@keyframes rotate-ccw { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
@keyframes rotate-cw { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes zoom-in { from { opacity: 0; transform: scale(0.5); } to { opacity: 1; transform: scale(1); } }

/* FIXED KEYFRAMES to include translate(-50%, -50%) at every step */
@keyframes bounce-in {
  0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
  60% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
  100% { transform: translate(-50%, -50%) scale(1); }
}

@media (max-width: 600px) {
  .card-placeholder { height: 120px; width: 80px; }
  .playing-card { height: 120px; width: 80px; }
  .table-surface { height: 90vw; top: 40%; width: 90vw; }
}
</style>
