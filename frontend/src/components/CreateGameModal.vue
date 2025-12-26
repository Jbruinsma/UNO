<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps<{
  isOpen: boolean;
  isLoading: boolean;
  userBalance: number;
}>();

const emit = defineEmits(['close', 'create']);

const MIN_BUY_IN = 1.00;

// Calculate 50% of the user's balance
const maxAllowedBuyIn = computed(() => {
  return Math.floor(props.userBalance * 0.5);
});

const maxPlayers = ref(4);
const buyIn = ref(0);
const buyInDisplay = ref("");
const error = ref<string | null>(null);


const canCreate = computed(() => {
  if (buyIn.value < MIN_BUY_IN) return false;
  if (buyIn.value > maxAllowedBuyIn.value) return false;
  return !(maxPlayers.value < 2 || maxPlayers.value > 10);
});

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num);
};

// Format Currency: 10000 -> "$10,000.00"
const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
};

// --- Input Handling ---

const handleBuyInInput = (event: Event) => {
  const input = event.target as HTMLInputElement;

  // 1. Get raw value and strip EVERYTHING except digits
  const originalValue = input.value;
  const numericString = originalValue.replace(/[^0-9]/g, '');

  // 2. Handle empty input
  if (!numericString) {
    buyIn.value = 0;
    buyInDisplay.value = "";
    error.value = null;
    return;
  }

  // 3. Convert to number
  let newValue = parseInt(numericString, 10);

  // 4. Update State
  buyIn.value = newValue;
  const formatted = formatNumber(newValue);
  buyInDisplay.value = formatted;

  // 5. Force input value update (removes letters immediately)
  // We use nextTick to ensure Vue re-renders the input with the clean value
  nextTick(() => {
    input.value = formatted;
  });

  // 6. Validate
  validate();
};

const validate = () => {
  if (buyIn.value > maxAllowedBuyIn.value) {
    error.value = `Limit Exceeded. Max (50% of balance): ${formatCurrency(maxAllowedBuyIn.value)}`;
  } else if (buyIn.value < MIN_BUY_IN && buyIn.value !== 0) {
    error.value = `Min buy-in is ${formatCurrency(MIN_BUY_IN)}`;
  } else {
    error.value = null;
  }
};

const setMaxBuyIn = () => {
  buyIn.value = maxAllowedBuyIn.value;
  buyInDisplay.value = formatNumber(maxAllowedBuyIn.value);
  validate();
};

const handleCreate = () => {
  validate();
  if (error.value) return;

  emit('create', {
    maxPlayers: maxPlayers.value,
    buyIn: buyIn.value
  });
};

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    buyIn.value = 0;
    buyInDisplay.value = "";
    error.value = null;
    maxPlayers.value = 4;
  }
});
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>Create New Table</h3>
        <button class="btn-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="modal-body">

        <div class="form-group">
          <div class="label-row">
            <label>Max Players</label>
            <span class="value-badge">{{ maxPlayers }}</span>
          </div>
          <input
            type="range"
            min="2"
            max="10"
            step="1"
            v-model.number="maxPlayers"
            class="range-slider"
          />
          <div class="range-labels">
            <span>2</span>
            <span>10</span>
          </div>
        </div>

        <div class="form-group">
          <div class="label-row">
            <label>Buy-In Amount</label>
            <button class="btn-max" @click="setMaxBuyIn">
              Max: {{ formatCurrency(maxAllowedBuyIn) }}
            </button>
          </div>

          <div class="input-wrapper" :class="{'error-border': error}">
            <span class="currency-prefix">$</span>
            <input
              type="text"
              inputmode="numeric"
              placeholder="0"
              :value="buyInDisplay"
              @input="handleBuyInInput"
              class="number-input"
            />
          </div>

          <div class="helper-text" v-if="!error">
            Min: {{ formatCurrency(MIN_BUY_IN) }}
          </div>
          <div class="error-text" v-else>
            {{ error }}
          </div>
        </div>

      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button
          class="btn-confirm"
          :disabled="!canCreate || isLoading"
          @click="handleCreate"
        >
          <span v-if="isLoading" class="spinner-sm"></span>
          <span v-else>Create Table</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}

.modal-content {
  background: #1f2937; border: 1px solid #374151; border-radius: 16px;
  width: 90%; max-width: 450px; color: white;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.3s ease-out;
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1.5rem; border-bottom: 1px solid #374151;
}
.modal-header h3 { margin: 0; font-size: 1.25rem; font-weight: 700; color: white; }

.btn-close {
  background: none; border: none; color: #9ca3af; font-size: 1.5rem;
  cursor: pointer; transition: color 0.2s;
}
.btn-close:hover { color: white; }

.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }

.form-group { display: flex; flex-direction: column; gap: 0.5rem; }

.label-row { display: flex; justify-content: space-between; align-items: center; }
label { color: #d1d5db; font-weight: 600; font-size: 0.9rem; }
.value-badge { background: #374151; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-family: monospace; }

.btn-max {
  background: rgba(250, 204, 21, 0.1); color: #facc15; border: 1px solid rgba(250, 204, 21, 0.2);
  border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; cursor: pointer; font-weight: bold;
  transition: all 0.2s;
}
.btn-max:hover { background: rgba(250, 204, 21, 0.2); }

.range-slider {
  width: 100%; -webkit-appearance: none; background: #374151; height: 6px; border-radius: 3px; outline: none;
}
.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px; background: #facc15; border-radius: 50%; cursor: pointer;
}
.range-labels { display: flex; justify-content: space-between; font-size: 0.8rem; color: #6b7280; margin-top: 4px; }

.input-wrapper {
  position: relative; display: flex; align-items: center;
  background: #111827; border: 1px solid #374151; border-radius: 8px;
  transition: border-color 0.2s;
}
.input-wrapper:focus-within { border-color: #facc15; }
.input-wrapper.error-border { border-color: #f87171; }

.currency-prefix {
  position: absolute; left: 12px; color: #9ca3af; font-weight: bold; pointer-events: none;
}

.number-input {
  width: 100%; background: transparent; border: none;
  color: white; padding: 12px 12px 12px 30px;
  font-family: 'Courier New', monospace; font-size: 1.1rem; font-weight: bold;
  outline: none;
}

.helper-text { font-size: 0.75rem; color: #6b7280; margin-top: 4px; text-align: right; }
.error-text { font-size: 0.75rem; color: #f87171; margin-top: 4px; text-align: right; font-weight: 600; }

.modal-footer {
  padding: 1.5rem; border-top: 1px solid #374151;
  display: flex; gap: 1rem; justify-content: flex-end;
}

.btn-cancel {
  background: transparent; border: 1px solid #4b5563; color: white;
  padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-cancel:hover { background: rgba(255,255,255,0.05); border-color: white; }

.btn-confirm {
  background: #facc15; border: none; color: #854d0e;
  padding: 10px 24px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; min-width: 100px;
}
.btn-confirm:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(250, 204, 21, 0.25); }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; filter: grayscale(1); }

.spinner-sm {
  width: 16px; height: 16px; border: 2px solid rgba(133, 77, 14, 0.3);
  border-left-color: #854d0e; border-radius: 50%; animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
