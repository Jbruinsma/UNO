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
const playerStates = ref<Record<string,"playing" | "ready">>({});

// Lobby State
const hostId = ref<string>("");
const players = ref<string[]>([]); // List of Player IDs
const playerNames = ref<Record<string, string>>({}); // Map: ID -> Name
const availableGames = ref<any[]>([]);

// --- In-Game State ---
const myHand = ref<string[]>([]);
const currentActiveColor = ref<string>("");
const topCard = ref<string>("");
const currentPlayerId = ref<string>("");
const direction = ref<number>(1); // 1 for clockwise, -1 for counter-clockwise
const otherPlayerCardCounts = ref<Record<string, number>>({}) // {uuid: cardCount}
const event = ref<Record<string, any>>({});
const lockDrawableCardPile = ref<boolean>(false);

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
      players.value = [];
      availableGames.value = [];
      currentGameId.value = null;
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

    console.log("Handling message:", data);

    switch (data.event) {

      // --- Global Lobby Events ---
      case "lobby_update":
        availableGames.value = data.games || [];
        break;

      case "player_back_to_lobby":
  if (data.player_states) playerStates.value = data.player_states;
  break;

      case "game_created":
        currentGameId.value = data.game_id;
        hostId.value = data.creator;
        players.value = data.players;
        playerNames.value = data.player_names;
        if (data.player_states) playerStates.value = data.player_states;
        gameState.value = "LOBBY";
        resetInGameState();
        break;

      case "player_joined":

        console.log("Player Joined:", data);

        players.value = data.players;
        playerNames.value = data.player_names;
        hostId.value = data.host_id;
        if (data.player_states) playerStates.value = data.player_states;

        if (data.new_player_id === playerId.value) {
          currentGameId.value = data.game_id;
          gameState.value = "LOBBY";
          resetInGameState();
        }
        break;

      case "player_left":
        players.value = players.value.filter((id) => id !== data.player_id);
        const newNames = { ...playerNames.value };
        delete newNames[data.player_id];
        playerNames.value = newNames;

        if (data.player_id === hostId.value && players.value.length > 0) {
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
           // @ts-expect-error
          hostId.value = players.value[0];
        }
        break;

      case "game_started":
        gameState.value = "PLAYING";

      case "game_update":
        console.log("Game Update:", data);
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
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "status_check" }));
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
      console.log("Leaving game...");
      socket.value.send(JSON.stringify({ action: "leave_game" }));
      console.log("JSON SENT")
      gameState.value = "LANDING";
      players.value = [];
      currentGameId.value = null;
      resetInGameState();
    } else {
      console.warn("Tried to leave game when not connected!");
    }
  };

  const startGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "start_game" }));
    }
  };

  const endGame = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "end_game" }));
    }
  };

  const backToLobby = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({ action: "back_to_lobby" }));
    }
  }

  const playCard = (card: string) => {
    console.log("Playing card:", card);
    if (socket.value) {
        socket.value.send(JSON.stringify({
          action: "process_turn",
          extra: {
            action: "play_card",
            card: card,
          }
        }));
    }
  };

  const drawCard = (advanceTurn: boolean = true) => {
    try {
      lockDrawableCardPile.value = true;
      console.log("Drawing card...");
      if (socket.value) { socket.value.send(JSON.stringify({action: "process_turn", extra: {action: "draw_card_from_middle", advance_turn: advanceTurn}})); }
    } catch (e) {
      console.log("Error drawing card:", e);
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
    // State
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
    players,
    playerNames,
    hostId,
    myHand,
    currentActiveColor,
    topCard,
    currentPlayerId,
    availableGames,

    // Computeds
    isHost,
    isMyTurn,

    // Actions
    initConnection,
    disconnect,
    statusCheck,
    createGame,
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
