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
        console.log("Player joined:", data);
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
        break;
      case "game_started":
        gameState.value = "PLAYING";
      case "error":
        currentError.value = data.message;
        setTimeout(() => (currentError.value = null), 5000);
        break;
    }
  };

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
    }
  };

  const startGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "start_game" }));
      gameState.value = "PLAYING";
    }
  };

  const isHost = computed(() => playerId.value === hostId.value);

  return {
    isConnected,
    currentError,
    playerId,
    playerName,
    currentGameId,
    gameState,
    players,
    playerNames,
    hostId,
    isHost,
    initConnection,
    disconnect,
    createGame,
    joinGame,
    leaveGame,
    startGame,
  };
}
