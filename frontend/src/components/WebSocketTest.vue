<template>
  <div class="max-w-xl mx-auto p-4">
    <h2 class="text-2xl font-semibold mb-4">WebSocket Test</h2>

    <div class="mb-3">
      <label class="block text-sm font-medium mb-1">Client ID</label>
      <input v-model="clientId" class="w-full border rounded px-3 py-2" />
    </div>

    <div class="flex items-center gap-3 mb-4">
      <button @click="connect" :disabled="status === 'Connected' || status === 'Connecting'" class="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50">Connect</button>
      <button @click="disconnect" :disabled="status === 'Disconnected'" class="px-4 py-2 bg-gray-600 text-white rounded disabled:opacity-50">Disconnect</button>

      <div class="ml-auto">
        <span :class="status === 'Connected' ? 'text-green-600' : 'text-red-600'" class="font-medium">{{ status }}</span>
      </div>
    </div>

    <div class="mb-4">
      <label class="block text-sm font-medium mb-1">Message</label>
      <div class="flex gap-2">
        <input v-model="messageInput" class="flex-1 border rounded px-3 py-2" @keyup.enter="sendMessage" placeholder="Type a message and press Enter" />
        <button @click="sendMessage" class="px-4 py-2 bg-green-600 text-white rounded">Send</button>
      </div>
    </div>

    <div>
      <h3 class="text-lg font-medium mb-2">Logs</h3>
      <div class="border rounded max-h-72 overflow-auto p-2 bg-white">
        <ul>
          <li v-for="log in logs" :key="log.id" class="mb-2 text-sm">
            <div class="text-xs text-gray-500">{{ log.timestamp }}</div>
            <div class="text-gray-800">{{ log.text }}</div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'

// Types & Interfaces
export type ConnectionStatus = 'Disconnected' | 'Connecting' | 'Connected'
export interface LogMessage {
  id: number
  text: string
  timestamp: string
}

// Reactive State
const status = ref<ConnectionStatus>('Disconnected')
const clientId = ref<string>('player-1')
const socket = ref<WebSocket | null>(null)
const messageInput = ref<string>('')
const logs = ref<LogMessage[]>([])
let nextId = 1

// Helpers
function pushLog(text: string) {
  logs.value.push({ id: nextId++, text, timestamp: new Date().toISOString() })
}

// Methods
function connect() {
  if (socket.value) return
  status.value = 'Connecting'
  const url = `ws://localhost:8000/ws/${encodeURIComponent(clientId.value)}`
  try {
    const ws = new WebSocket(url)
    socket.value = ws

    ws.addEventListener('open', () => {
      status.value = 'Connected'
      pushLog(`Connection opened to ${url}`)
    })

    ws.addEventListener('message', (ev: MessageEvent) => {
      // Try to parse message; accept plain text
      let text: string
      try {
        text = typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data)
      } catch {
        // fallback if JSON.stringify throws
        text = String(ev.data)
      }
      pushLog(text)
    })

    ws.addEventListener('close', () => {
      status.value = 'Disconnected'
      socket.value = null
      pushLog('Connection closed')
    })

    ws.addEventListener('error', () => {
      pushLog('WebSocket error')
    })
  } catch (err) {
    status.value = 'Disconnected'
    pushLog('Failed to create WebSocket: ' + String(err))
  }
}

function sendMessage() {
  if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
    pushLog('Cannot send message: socket not open')
    return
  }
  const text = messageInput.value.trim()
  if (!text) return
  socket.value.send(text)
  pushLog(`Sent: ${text}`)
  messageInput.value = ''
}

function disconnect() {
  if (socket.value) {
    socket.value.close()
    // close handler will set socket to null and update status
  } else {
    status.value = 'Disconnected'
  }
}

// Lifecycle
onUnmounted(() => {
  if (socket.value) {
    socket.value.close()
  }
})
</script>

<style scoped>
/* Fallback styles if Tailwind isn't present */
.max-w-xl { max-width: 40rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.p-4 { padding: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: .75rem; }
.mb-2 { margin-bottom: .5rem; }
.border { border: 1px solid #e5e7eb; }
.rounded { border-radius: .375rem; }
.px-3 { padding-left: .75rem; padding-right: .75rem; }
.py-2 { padding-top: .5rem; padding-bottom: .5rem; }
.bg-white { background: #fff; }
</style>
