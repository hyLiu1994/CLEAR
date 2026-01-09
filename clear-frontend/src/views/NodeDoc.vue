<template>
  <AppPageLayout>
    <section class="panel panel--doc">
      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>{{ loadingMessage }}</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <h3>Error Loading Node</h3>
        <p>{{ error }}</p>
        <button @click="retryLoading" class="retry-btn">Retry</button>
      </div>

      <!-- Normal display -->
      <template v-else-if="node">
        <!-- Top: Breadcrumbs, switch text based on type -->
        <header class="panel-header doc-header">
          <div class="breadcrumbs">
            <span class="crumb" @click="goMap">Map</span>
            <span class="crumb-sep">/</span>

            <!-- Non-segment: SD-KG path; segment: Segment path -->
            <template v-if="node.type === 'segment'">
              <span class="crumb current">{{ nodeId }}</span>
            </template>
            <template v-else>
              <span class="crumb" @click="goSDKG">SD-KG</span>
              <span class="crumb-sep">/</span>
              <span class="crumb current">{{ nodeId }}</span>
            </template>
          </div>

          <span class="type-pill">
            {{ typeLabel }}
          </span>
        </header>

        <!-- Main area: Select layout component based on type -->
        <div class="panel-body">
          <div class="doc-inner">
            <component
              :is="activeComponent"
              :node-id="nodeId"
              :node="node"
              :current-level="currentLevel"
              :loading-level="loadingLevel"
              @view-map="handleViewMap"
              @open-node="handleOpenNode"
              @switch-level="handleLoadLevel"
            />
          </div>
        </div>
      </template>

      <!-- Empty data state -->
      <div v-else class="empty-state">
        <h3>Node Not Found</h3>
        <p>The requested node could not be loaded.</p>
        <button @click="goSDKG" class="back-btn">Back to SD-KG</button>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppPageLayout from '../components/AppPageLayout.vue'
import NodeDocSegment from '../components/node-doc/NodeDocSegment.vue'
import NodeDocGeneric from '../components/node-doc/NodeDocGeneric.vue'

const route = useRoute()
const router = useRouter()

// Reactive data
const node = ref(null)
const loading = ref(false)
const error = ref(null)
const lastLoadedId = ref('')
const currentLevel = ref(3) 
const loadingLevel = ref(null) 

let isLoading = false

// Current node ID
const nodeId = computed(() => (route.params.id ?? 'UNKNOWN').toString())

const loadingMessage = computed(() => {
  if (loadingLevel.value) {
    return `Loading level ${loadingLevel.value} relationships...`
  }
  return 'Loading node details...'
})


async function loadNodeData(id) {
  if (isLoading || lastLoadedId.value === id) {
    console.log('Skipping duplicate load for:', id)
    return
  }

  if (!id || id === 'UNKNOWN') {
    error.value = 'Invalid node ID'
    return
  }

  try {
    isLoading = true
    loading.value = true
    error.value = null
    lastLoadedId.value = id

    console.log(`Loading node data: ${id}`)

    const [nodeDetail, subgraphData] = await Promise.all([
      fetchNodeDetail(id),
      fetchSubgraphData(id)
    ])

    const enhancedNode = {
      ...nodeDetail,
      graph: subgraphData,
      currentMaxLevel: subgraphData.maxLevel 
    }

    node.value = enhancedNode
    console.log(`Node loaded successfully: ${id}, subgraph nodes: ${subgraphData.totalNodes}`)

  } catch (err) {
    error.value = err.message
    console.error('Error loading node:', err)
  } finally {
    loading.value = false
    loadingLevel.value = null
    isLoading = false
  }
}

async function fetchNodeDetail(nodeId) {
  const nodeUrl = `http://localhost:8000/api/v1/sdkg/nodes/${nodeId}`
  const response = await fetch(nodeUrl)
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Node "${nodeId}" not found`)
    }
    throw new Error(`Failed to load node details: ${response.status}`)
  }
  
  return await response.json()
}

async function fetchSubgraphData(nodeId) {
  const subgraphUrl = `http://localhost:8000/api/v1/sdkg/subgraph/${nodeId}`
  const response = await fetch(subgraphUrl)
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Subgraph for node "${nodeId}" not found`)
    }
    throw new Error(`Failed to load subgraph: ${response.status}`)
  }
  
  return await response.json()
}

const handleLoadLevel = (level) => {
  console.log('Switching to level:', level)
  currentLevel.value = level
}

// Retry loading
function retryLoading() {
  loadNodeData(nodeId.value)
}

// Load data when the component is mounted
onMounted(() => {
  loadNodeData(nodeId.value)
})

// Watch for route changes (when the user directly switches nodes)
watch(nodeId, (newId, oldId) => {
  if (newId !== oldId) {
    console.log('Route changed from', oldId, 'to', newId)
    currentLevel.value = 3 
    loadNodeData(newId)
  }
})

// Type → Label
const typeLabel = computed(() => {
  if (!node.value) return 'Loading...'
  
  switch (node.value.type) {
    case 'behavior':
      return 'Behavior'
    case 'attribute':
      return 'Attribute'
    case 'function':
      return 'Function'
    case 'segment':
      return 'Segment'
    case 'trajectory':
      return 'Trajectory'
    default:
      return 'Node'
  }
})

// Select specific layout component
const activeComponent = computed(() => {
  if (!node.value) return null
  
  if (node.value.type === 'segment') return NodeDocSegment
  return NodeDocGeneric
})

// Navigation functions
const goMap = () => router.push('/map')
const goSDKG = () => router.push('/sdkg')

// Handle "view-map" event emitted by child components
const handleViewMap = () => {
  if (!node.value) return
  
  if (node.value.type === 'segment') {
    router.push({ path: '/map', query: { focusSegment: nodeId.value } })
  } else {
    router.push({ path: '/map', query: { focusNode: nodeId.value } })
  }
}

// "open-node" event emitted by child components (related node click)
const handleOpenNode = (id) => {
  if (id && id !== nodeId.value) {
    console.log('Opening node:', id)
    router.push(`/node/${id}`)
  }
}
</script>

<style scoped>
.panel {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e5e5e5, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

.panel--doc {
  max-width: 960px;
  margin: 0 auto;
}

.panel-header {
  padding: 14px 20px 10px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.doc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breadcrumbs {
  font-size: 12px;
  color: #6b7280;
}

.crumb {
  cursor: pointer;
}

.crumb.current {
  cursor: default;
  color: #9ca3af;
}

.crumb:hover:not(.current) {
  color: #111827;
}

.crumb-sep {
  margin: 0 4px;
}

.type-pill {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6b7280;
}

.panel-body {
  flex: 1;
  padding: 16px 20px 18px 20px;
  box-sizing: border-box;
  background: #f9fafb;
  overflow-y: auto;
}

.doc-inner {
  max-width: 720px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state p {
  margin: 0;
  font-size: 14px;
}

.error-state {
  padding: 60px 20px;
  text-align: center;
  color: #dc2626;
}

.error-state h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
}

.error-state p {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: #6b7280;
}

.retry-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: #2563eb;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #6b7280;
}

.empty-state h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
}

.empty-state p {
  margin: 0 0 20px 0;
  font-size: 14px;
}

.back-btn {
  padding: 8px 16px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  background: #4b5563;
}
</style>