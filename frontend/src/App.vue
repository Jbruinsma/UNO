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
  </main>
</template>

<style>
body { margin: 0; padding: 0; }
</style>

Now, when you click **Create Game**, the backend will reply, the composable will switch `gameState` to `'LOBBY'`, and `App.vue` will automatically swap the UI from the landing page to the "Lobby Placeholder".
