<script setup lang="ts">
import HomeLanding from '../components/LandingPage.vue';
import { useGameWebSocket } from '../composables/useGameWebSocket';
import Lobby from "@/components/Lobby.vue";
import GameTable from "@/components/GameTable.vue";
import { useRouter } from 'vue-router';

const { gameState } = useGameWebSocket();
const router = useRouter();

const navigateToLogin = () => {
  router.push('/login');
};
</script>

<template>
  <div class="game-container">
    <HomeLanding
      v-if="gameState === 'LANDING'"
      @login="navigateToLogin"
    />

    <div v-else-if="gameState === 'LOBBY'" class="lobby-placeholder">
      <Lobby></Lobby>
    </div>

    <div v-else-if="gameState === 'PLAYING'" class="game-placeholder">
      <GameTable></GameTable>
    </div>
  </div>
</template>

<style scoped>
</style>
