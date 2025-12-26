import { createRouter, createWebHistory } from 'vue-router'
import LoginRegister from "@/views/LoginRegister.vue";
import GameView from "@/views/GameView.vue";
import Dashboard from "@/views/Dashboard.vue";
import SoloView from "@/views/SoloView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: GameView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginRegister
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/solo',
      name: 'solo',
      component: SoloView
    }
  ],
})

export default router
