export type Game = {
  gameId: string,
  hostName: string,
  playerCount: number,
  maxPlayers: number,
  buyIn: number,
  isActive: boolean
};

export type GameState = "LANDING" | "LOBBY" | "PLAYING";

export type SoloGameSettings = {
  turnTimer: number,
  stackingMode: string,
  afkBehavior: string,
  forfeitAfterSkips: boolean
};
