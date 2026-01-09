// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Map from '../views/Map.vue'
import SDKG from '../views/SDKG.vue'
import NodeDoc from '../views/NodeDoc.vue'
import Home from '../views/Home.vue'
import Settings from '../views/Settings.vue'

const routes = [
  { path: '/', redirect: '/Home' },
  {
    path: '/map',
    name: 'Map',
    component: Map,
  },
  { 
    path: '/sdkg', 
    name: 'SDKG', 
    component: SDKG 
  },
  { 
    path: '/node/:id', 
    name: 'NodeDoc', 
    component: NodeDoc 
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
