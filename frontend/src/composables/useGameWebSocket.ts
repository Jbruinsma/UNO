import { ref, computed } from "vue";

// Global state (Singleton)
const socket = ref<WebSocket | null>(null);
const isConnected = ref(false);
const currentError = ref<string | null>(null);

// Game State
const playerId = ref<string>("");
const playerName = ref<string>("");
const currentGameId = ref<string | null>(null);
const gameState = ref<"LANDING" | "LOBBY" | "PLAYING">("LANDING");

// Lobby State
const hostId = ref<string>("");
const players = ref<string[]>([]); // List of Player IDs
const playerNames = ref<Record<string, string>>({}); // Map: ID -> Name

// --- NEW: In-Game State ---
const myHand = ref<string[]>([]);
const topCard = ref<string>("");
const currentPlayerId = ref<string>("");
const direction = ref<number>(1); // 1 for clockwise, -1 for counter-clockwise
const otherPlayerCardCounts = ref<Record<string, number>>({}) // {uuid: cardCount}

export function useGameWebSocket() {

  const initConnection = (displayName: string) => {
    if (socket.value?.readyState === WebSocket.OPEN) return;

    let storedId = localStorage.getItem("uno_player_id");
    if (!storedId) {
      storedId = "user_" + Math.floor(Math.random() * 10000);
      localStorage.setItem("uno_player_id", storedId);
    }
    playerId.value = storedId;
    playerName.value = displayName;

    const safeName = encodeURIComponent(displayName);
    socket.value = new WebSocket(
      `ws://localhost:8000/ws/${playerId.value}/${safeName}`,
    );

    socket.value.onopen = () => {
      isConnected.value = true;
      currentError.value = null;
    };

    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
      } catch (e) {
        console.log("Raw message:", event.data);
      }
    };

    socket.value.onclose = () => {
      isConnected.value = false;
    };
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.close();
      socket.value = null;
      isConnected.value = false;
    }
  };

  const handleMessage = (data: any) => {
    switch (data.event) {
      case "game_created":
        currentGameId.value = data.game_id;
        hostId.value = data.creator;
        players.value = data.players;
        playerNames.value = data.player_names;
        gameState.value = "LOBBY";
        break;

      case "player_joined":
        players.value = data.players;
        playerNames.value = data.player_names;
        hostId.value = data.host_id;
        // If I am the one joining, switch to lobby
        if (data.new_player_id === playerId.value) {
          currentGameId.value = data.game_id;
          gameState.value = "LOBBY";
        }
        break;

      case "player_left":
        players.value = players.value.filter((id) => id !== data.player_id);
        delete playerNames.value[data.player_id];
        // If host left, frontend temp fix (backend should handle real logic)
        if (data.player_id === hostId.value && players.value.length > 0) {
           hostId.value = players.value[0];
        }
        break;

      // --- NEW: Game Logic Handling ---
      case "game_started":
        gameState.value = "PLAYING";
      case "game_update":
        if (data.top_card) topCard.value = data.top_card;
        if (data.current_player) currentPlayerId.value = data.current_player;
        if (data.hand) myHand.value = data.hand;
        if (data.direction) direction.value = data.direction;
        if (data.card_counts) otherPlayerCardCounts.value = data.card_counts;
        break;

      case "error":
        currentError.value = data.message;
        setTimeout(() => (currentError.value = null), 5000);
        break;
    }
  };

  // --- Actions ---

  const createGame = (displayName: string) => {
    if (!socket.value) initConnection(displayName);
    setTimeout(() => {
      socket.value?.send(JSON.stringify({ action: "create_game" }));
    }, 100);
  };

  const joinGame = (gameId: string, displayName: string) => {
    if (!socket.value) initConnection(displayName);
    setTimeout(() => {
      socket.value?.send(
        JSON.stringify({ action: "join_game", game_id: gameId }),
      );
    }, 100);
  };

  const leaveGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "leave_game" }));
      gameState.value = "LANDING";
      players.value = [];
      currentGameId.value = null;
      myHand.value = [];
    }
  };

  const startGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "start_game" }));
    }
  };

  // --- NEW: In-Game Actions ---
  const playCard = (card: string) => {
    if (socket.value) {
        socket.value.send(JSON.stringify({
            action: "play_card",
            card: card
        }));
    }
  };

  const drawCard = () => {
    if (socket.value) {
        socket.value.send(JSON.stringify({ action: "draw_card" }));
    }
  };

  // --- Computeds ---
  const isHost = computed(() => playerId.value === hostId.value);
  const isMyTurn = computed(() => playerId.value === currentPlayerId.value);

  return {
    // State
    isConnected,
    currentError,
    playerId,
    playerName,
    currentGameId,
    direction,
    otherPlayerCardCounts,
    gameState,
    players,
    playerNames,
    hostId,
    myHand,
    topCard,
    currentPlayerId,

    // Computeds
    isHost,
    isMyTurn,

    // Actions
    initConnection,
    disconnect,
    createGame,
    joinGame,
    leaveGame,
    startGame,
    playCard,
    drawCard
  };
}
