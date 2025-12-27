import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import type {Game, GameState, SoloGameSettings} from "@/types.ts";

// Global state (Singleton)
const socket = ref<WebSocket | null>(null);
const isConnected = ref<boolean>(false);
const currentError = ref<string | null>(null);

// Game State
const playerId = ref<string>("");
const playerName = ref<string>("");
const currentGameId = ref<string | null>(null);
const gameState = ref<GameState>("LANDING");
const playerStates = ref<Record<string,"playing" | "ready">>({});
const gameSettings = ref<SoloGameSettings>({
  turnTimer: 30,
  stackingMode: 'off',
  afkBehavior: 'draw_skip',
  forfeitAfterSkips: true
});

// Lobby State
const hostId = ref<string>("");
const players = ref<string[]>([]);
const playerNames = ref<Record<string, string>>({});
const availableGames = ref<Game[]>([]);

// --- In-Game State ---
const myHand = ref<string[]>([]);
const currentActiveColor = ref<string>("");
const topCard = ref<string>("");
const currentPlayerId = ref<string>("");
const direction = ref<number>(1);
const otherPlayerCardCounts = ref<Record<string, number>>({})
const event = ref<Record<string, any>>({});
const lockDrawableCardPile = ref<boolean>(false);

export function useSoloGameWebSocket() {
  const router = useRouter();

  const initConnection = (displayName: string) => {
    // 1. Prevent double connections
    if (socket.value?.readyState === WebSocket.OPEN) return;

    const token = localStorage.getItem('token');
    if (!token) {
      console.error("No access token found. Redirecting to login.");
      if (router) router.push('/login');
      return;
    }

    const gameTypeId = 'SOLO';
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const apiHost = window.location.hostname;
    const apiPort = '8000';
    const wsUrl = `${protocol}://${apiHost}:${apiPort}/games/${gameTypeId}/ws?token=${token}`;

    console.log(`Connecting to Backend: ${wsUrl}`);
    socket.value = new WebSocket(wsUrl);

    socket.value.onopen = () => {
      console.log("Connected to Solo Lobby WebSocket");
      isConnected.value = true;
      currentError.value = null;
      playerName.value = displayName;
    };

    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    socket.value.onclose = (event) => {
      console.log("WebSocket Closed", event.code, event.reason);
      isConnected.value = false;
      players.value = [];
      availableGames.value = [];

      if (event.code === 1008 || event.code === 403) {
        currentError.value = "Session expired. Please log in again.";
        if(router) router.push('/auth/login');
      } else if (!event.wasClean) {
        currentError.value = "Connection lost.";
      }
    };

    socket.value.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.onclose = null;

      socket.value.close();
      socket.value = null;
      isConnected.value = false;
    }
  };

  const resetGameSettings = () => {
    gameSettings.value = {
      turnTimer: 30,
      stackingMode: 'off',
      afkBehavior: 'draw_skip',
      forfeitAfterSkips: true
    };
  }

  const handleMessage = (data: any) => {
    // Console log reduced to avoid noise, uncomment for debug
    console.log("Received:", data);

    switch (data.event) {
      case "lobby_update":
        availableGames.value = data.games || [];
        console.log(isConnected.value);
        break;

      case "system":
        if (data.message && data.message.startsWith("Welcome")) {
            const name = data.message.split(' ')[1];
            if(name) playerName.value = name;
        }
        break;

        case "game_created":

          // {
          //   "event": "game_created",
          //   "game_id": "QZPD",
          //   "creator": "278a16a9-aaa9-49b0-b567-8d7a5caa5738",
          //   "players": [
          //     "278a16a9-aaa9-49b0-b567-8d7a5caa5738"
          // ],
          //   "player_names": {
          //     "278a16a9-aaa9-49b0-b567-8d7a5caa5738": "justin"
          // },
          //   "message": "Room QZPD created."
          // }

          currentGameId.value = data.gameId;
          hostId.value = data.creator;
          players.value = data.players;
          playerNames.value = data.playerNames;
          playerStates.value = data.playerStates;
          gameState.value = "LOBBY";
          resetInGameState();
          break;

      case "game_joined":
        console.log(`Joined game ${data.game_id}`);
        currentGameId.value = data.game_id;
        if (data.creator) hostId.value = data.creator;
        if (data.host_id) hostId.value = data.host_id;
        if (data.players) players.value = data.players;
        if (data.player_names) playerNames.value = data.player_names;
        if (data.player_states) playerStates.value = data.player_states;
        gameState.value = "LOBBY";
        resetInGameState();
        break;

      case "player_back_to_lobby":
        if (data.player_states) playerStates.value = data.player_states;
        break;

      case "game_settings_saved":
        const updatedSettings = data.settings;
        gameSettings.value = {
          turnTimer: updatedSettings.turn_timeout_seconds,
          stackingMode: updatedSettings.stacking_mode,
          afkBehavior: updatedSettings.afk_behavior,
          forfeitAfterSkips: updatedSettings.max_afk_strikes > 0
        };
        break;

      case "player_joined":
        players.value = data.players;
        playerNames.value = data.player_names;
        hostId.value = data.host_id;
        if (data.player_states) playerStates.value = data.player_states;
        break;

      case "player_left":
        players.value = players.value.filter((id) => id !== data.player_id);
        const newNames = { ...playerNames.value };
        delete newNames[data.player_id];
        playerNames.value = newNames;
        if (data.player_id === hostId.value && players.value.length > 0) {
          // @ts-expect-error type safety
          hostId.value = players.value[0];
        }
        break;

      case "game_started":
        gameState.value = "PLAYING";
        // Fallthrough

      case "game_update":
        if (data.current_active_color) currentActiveColor.value = data.current_active_color;
        if (data.top_card) topCard.value = data.top_card;
        if (data.current_player) currentPlayerId.value = data.current_player;
        if (data.hand) myHand.value = data.hand;
        if (data.card_counts) otherPlayerCardCounts.value = data.card_counts;
        if (data.player_states) playerStates.value = data.player_states;
        if (data.direction) {
          const newDirection = data.direction;
          if ([-1, 1].includes(newDirection) && newDirection !== direction.value) direction.value = newDirection;
        }
        if (data.game_event) event.value = data.game_event;
        break;

      case "error":
        console.error("Server Error:", data.message);
        currentError.value = data.message;
        setTimeout(() => (currentError.value = null), 5000);
        break;
    }
  };

  const resetInGameState = () => {
    myHand.value = [];
    topCard.value = "";
    currentActiveColor.value = "";
    event.value = {};
    direction.value = 1;
  };

  // --- Actions ---

  const statusCheck = () => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({ action: "status_check" }));
    }
  };

  const createGame = (options: { maxPlayers: number; buyIn: number; isPrivate: boolean }) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({
        action: "create_game",
        extra: { max_players: options.maxPlayers, buy_in: options.buyIn , is_private: options.isPrivate}
      }));
    }
  };

  const saveGameSettings = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "save_game_settings", extra: {settings: gameSettings.value} }));
    }
  };

  const joinGame = (gameId: string) => {
    // Simple retry logic if socket is connecting
    const sendMessage = () => {
      if (socket.value && socket.value.readyState === WebSocket.OPEN) {
         socket.value.send(JSON.stringify({ action: "join_game", game_id: gameId }));
      } else if (socket.value && socket.value.readyState === WebSocket.CONNECTING) {
         setTimeout(sendMessage, 200);
      }
    }
    sendMessage();
  };

  const leaveGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "leave_game" }));
      resetGameSettings();
      gameState.value = "LANDING";
      players.value = [];
      currentGameId.value = null;
      resetInGameState();
    }
  };

  const startGame = () => {
    if (socket.value) socket.value.send(JSON.stringify({ action: "start_game" }));
  };

  const endGame = () => {
    if (socket.value) socket.value.send(JSON.stringify({ action: "end_game" }));
  };

  const backToLobby = () => {
    if (socket.value) socket.value.send(JSON.stringify({ action: "back_to_lobby" }));
  }

  const playCard = (card: string) => {
    if (socket.value) {
        socket.value.send(JSON.stringify({
          action: "process_turn",
          extra: { action: "play_card", card: card }
        }));
    }
  };

  const drawCard = (advanceTurn: boolean = true) => {
    try {
      lockDrawableCardPile.value = true;
      if (socket.value) { socket.value.send(JSON.stringify({action: "process_turn", extra: {action: "draw_card_from_middle", advance_turn: advanceTurn}})); }
    } finally {
      lockDrawableCardPile.value = false;
    }
  };

  const changeColorWithWild = (color: string) => {
    if (socket.value) { socket.value.send(JSON.stringify({action: "process_turn", extra: {action: "change_color_with_wild", card: color}})); }
  }

  const changeColorWithWildAndDraw4 = (color: string) => {
    if (socket.value) { socket.value.send(JSON.stringify({action: "process_turn", extra: {action: "change_color_with_wild_and_draw4", card: color}})); }
  }

  const isHost = computed(() => playerId.value === hostId.value);
  const isMyTurn = computed(() => playerId.value === currentPlayerId.value);

  return {
    isConnected,
    currentError,
    playerId,
    playerName,
    currentGameId,
    direction,
    otherPlayerCardCounts,
    event,
    gameState,
    playerStates,
    gameSettings,
    players,
    playerNames,
    hostId,
    myHand,
    currentActiveColor,
    topCard,
    currentPlayerId,
    availableGames,
    isHost,
    isMyTurn,
    initConnection,
    disconnect,
    statusCheck,
    createGame,
    saveGameSettings,
    joinGame,
    leaveGame,
    startGame,
    endGame,
    backToLobby,
    playCard,
    drawCard,
    changeColorWithWild,
    changeColorWithWildAndDraw4,
  };
}
