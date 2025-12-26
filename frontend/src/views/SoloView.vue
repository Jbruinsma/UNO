<script setup lang="ts">
import { useSoloGameWebSocket } from '../composables/useSoloGameWebSocket.ts';
import Lobby from "@/components/Lobby.vue";
import GameTable from "@/components/GameTable.vue";
import { useRouter } from 'vue-router';
import LobbySelection from "@/components/LobbySelection.vue";

const { gameState } = useSoloGameWebSocket();
const router = useRouter();

const navigateToLogin = () => {
  router.push('/login');
};
</script>

<template>
  <div class="game-container">
    <lobby-selection
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
