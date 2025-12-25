<script setup lang="ts">
import { ref, computed } from 'vue';

const isLoginMode = ref(true);
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMsg = ref('');

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value;
  errorMsg.value = '';
  username.value = '';
  password.value = '';
  confirmPassword.value = '';
};

const isValid = computed(() => {
  if (isLoginMode.value) {
    return username.value.length > 0 && password.value.length > 0;
  }
  return (
    username.value.length > 0 &&
    password.value.length > 0 &&
    password.value === confirmPassword.value
  );
});

const handleSubmit = () => {
  if (!isValid.value) return;

  const payload = {
    username: username.value,
    password: password.value
  };

  if (isLoginMode.value) {
    console.log("Logging in with:", payload);
  } else {
    console.log("Registering with:", payload);
  }
};
</script>

<template>
  <div class="login-container">

    <header class="top-nav">
      <a href="/" class="back-link">← Back to Home</a>
    </header>

    <div class="content-box">
      <h1 class="title">ANTE <span class="badge">ONLINE</span></h1>

      <h2 class="subtitle">{{ isLoginMode ? 'Welcome Back' : 'Create Account' }}</h2>
      <p class="subtext">
        {{ isLoginMode ? 'Enter your credentials to access your account.' : 'Join the community and track your stats.' }}
      </p>

      <form @submit.prevent="handleSubmit" class="form-group">

        <div class="input-wrapper">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="text-input"
            placeholder="Username"
          />
        </div>

        <div class="input-wrapper">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="text-input"
            placeholder="Password"
          />
        </div>

        <div v-if="!isLoginMode" class="input-wrapper">
          <label for="confirm">Confirm Password</label>
          <input
            id="confirm"
            v-model="confirmPassword"
            type="password"
            class="text-input"
            placeholder="Confirm Password"
          />
        </div>

        <div v-if="errorMsg" class="error-banner">
          {{ errorMsg }}
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="!isValid"
        >
          {{ isLoginMode ? 'Log In' : 'Sign Up' }}
        </button>

      </form>

      <div class="toggle-section">
        <p>
          {{ isLoginMode ? "Don't have an account?" : "Already have an account?" }}
          <button @click="toggleMode" class="link-btn">
            {{ isLoginMode ? 'Register here' : 'Login here' }}
          </button>
        </p>
      </div>

    </div>
  </div>
</template>

<style scoped>
.back-link { color: #9ca3af; font-size: 0.9rem; font-weight: 600; text-decoration: none; transition: color 0.2s; }
.back-link:hover { color: white; }
.badge { background: #facc15; border-radius: 20px; color: #854d0e; font-size: 0.9rem; letter-spacing: 0; padding: 4px 10px; vertical-align: middle; }
.btn { border: none; border-radius: 12px; cursor: pointer; font-size: 1rem; font-weight: bold; padding: 12px; transition: all 0.2s; }
.btn:active { transform: scale(0.98); }
.btn:disabled { background: #e5e7eb; box-shadow: none; color: #9ca3af; cursor: not-allowed; opacity: 0.5; }
.btn-primary { background: #1f2937; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); color: white; margin-top: 1rem; width: 100%; }
.btn-primary:hover:not(:disabled) { background: #374151; transform: translateY(-1px); }
.content-box { background: white; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); max-width: 400px; padding: 2.5rem; text-align: center; width: 100%; }
.error-banner { background: #fee2e2; border-radius: 8px; color: #991b1b; font-size: 0.9rem; font-weight: 600; margin-top: 20px; padding: 12px; text-align: center; }
.form-group { display: flex; flex-direction: column; gap: 1.2rem; margin-top: 1.5rem; }
.input-wrapper { text-align: left; }
.input-wrapper label { color: #4b5563; display: block; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 0.5rem; text-transform: uppercase; }
.link-btn { background: none; border: none; color: #1f2937; cursor: pointer; font-weight: bold; text-decoration: underline; }
.link-btn:hover { color: #4b5563; }
.login-container { align-items: center; background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%); display: flex; flex-direction: column; font-family: 'Segoe UI', sans-serif; justify-content: center; min-height: 100vh; padding: 1rem; position: relative; }
.subtitle { color: #111827; font-size: 1.5rem; margin: 0 0 0.5rem 0; }
.subtext { color: #6b7280; font-size: 0.9rem; margin: 0; }
.text-input { border: 2px solid #e5e7eb; border-radius: 12px; box-sizing: border-box; font-size: 1.1rem; outline: none; padding: 12px; transition: border-color 0.2s; width: 100%; }
.text-input:focus { border-color: #1f2937; }
.title { color: #1f2937; font-size: 2rem; font-weight: 800; letter-spacing: -2px; margin: 0 0 1.5rem 0; }
.toggle-section { color: #6b7280; font-size: 0.9rem; margin-top: 1.5rem; }
.top-nav { left: 0; padding: 2rem; position: absolute; top: 0; width: 100%; }
</style>
