<script setup lang="ts">
import WebSocketTest from './components/WebSocketTest.vue'
</script>

<template>
  <div class="p-4">
    <h1>You did it!</h1>
    <p>
      Visit <a href="https://vuejs.org/" target="_blank" rel="noopener">vuejs.org</a> to read the
      documentation
    </p>

    <!-- Render the WebSocket test component -->
    <WebSocketTest />
  </div>
</template>

<style scoped></style>
