<script setup lang="ts">
import HomeLanding from './components/LandingPage.vue';
import { useGameWebSocket } from './composables/useGameWebSocket';
import Lobby from "@/components/Lobby.vue";

// We import the state here to decide what to render
const { gameState, currentGameId } = useGameWebSocket();
</script>

<template>
  <main>
    <!-- Landing Page -->
    <HomeLanding v-if="gameState === 'LANDING'" />

    <!-- Lobby -->
    <div v-else-if="gameState === 'LOBBY'" class="lobby-placeholder">
      <Lobby></Lobby>
    </div>

    <!-- Game In Progress -->
    <div v-else-if="gameState === 'PLAYING'" class="game-placeholder">
      <h1>Game In Progress</h1>
      <p>Game ID: {{ currentGameId }}</p>
    </div>

  </main>
</template>

<style>
body { margin: 0; padding: 0; }
</style>
