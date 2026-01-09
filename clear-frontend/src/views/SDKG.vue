<template>
  <AppPageLayout>
    <section class="panel">
      <header class="panel-header">
        <div>
          <h2 class="section-title">Structured Data-derived Knowledge Graph</h2>
        </div>
        <!-- Loading state indicator -->
        <div v-if="isLoading" class="loading-indicator">
          Loading graph data...
        </div>
      </header>

      <div class="panel-body">
        <div class="graph-wrapper" ref="graphWrapper" @click="onGraphAreaClick">
          <div ref="graphEl" class="graph-canvas"></div>

          <!-- Enhanced FloatingFilter -->
          <FloatingFilter
            v-model="showFilter"
            title="Filter"
            @apply="applyFilters"
            @reset="resetFilters"
            @toggle="resetView"
          >
            <!-- Keyword filter -->
            <div class="field">
              <label class="field-label">Keyword</label>
              <input
                v-model="filters.keyword"
                class="field-input"
                type="text"
                placeholder="Behavior / attribute / vessel id..."
              />
            </div>

            <!-- Node types: elegant button group -->
            <div class="field">
              <label class="field-label">Node types</label>
              <div class="button-group">
                <button
                  v-for="type in availableNodeTypes"
                  :key="type"
                  class="type-button"
                  :class="{ 'type-button-active': filters.nodeTypes.includes(type) }"
                  @click="toggleNodeType(type)"
                  :style="{
                    '--type-color': TYPE_COLORS[type] || TYPE_COLORS.default
                  }"
                >
                  <span class="button-text">{{ type }}</span>
                </button>
              </div>
            </div>
          </FloatingFilter>
        </div>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import ForceGraphModule from 'force-graph'

import AppPageLayout from '../components/AppPageLayout.vue'
import FloatingFilter from '../components/FloatingFilter.vue'

const ForceGraph = ForceGraphModule.default || ForceGraphModule

const graphEl = ref(null)
const graphWrapper = ref(null)
const router = useRouter()
let fg = null

const PERFORMANCE_CONFIG = {
  MAX_NODES: 20000,
  MAX_LINKS: 100000,
  NODE_RADIUS: 2, 
  PAGE_SIZE: 1000,
  SIMULATION_QUALITY: 'low',
  RENDER_QUALITY: 'low'
}

// Loading state
const isLoading = ref(false)
const isDataLoaded = ref(false)
const isGraphInitialized = ref(false)
const isFirstLoad = ref(true)

// Filter UI state
const showFilter = ref(false)

// Filter conditions
const filters = reactive({
  keyword: '',
  nodeTypes: []
})

// Optimized: Simplified data structure
const rawGraphData = ref({
  nodes: [],
  links: []
})

let fullGraphData = null
let currentGraphData = null

// Highlight state
let highlightNodes = new Set()
let highlightLinks = new Set()
let draggedNode = null

// Colors for different node types
const TYPE_COLORS = {
  behavior: '#3b82f6',      // 主蓝色 - 与连边同色系
  attribute: '#0ea5e9',     // 浅蓝色
  function: '#06b6d4',      // 青色
  segment: '#6366f1',       // 靛蓝色
  trajectory: '#8b5cf6',    // 蓝紫色
  default: '#64748b'        // 中性灰色
}
const LINK_COLORS = {
  default: 'rgba(59, 130, 246, 0.1)',
  highlighted: '#fbbf24'
}

const HIGHLIGHT_COLORS = {
  link: '#fbbf24'
}

// Computed properties: Available filter options (limited to 5 types)
const availableNodeTypes = computed(() => {
  const types = new Set()
  rawGraphData.value.nodes?.forEach(n => {
    if (n.type) types.add(n.type)
  })
  return Array.from(types).sort().slice(0, 5)
})

function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Button group methods
const toggleNodeType = (type) => {
  const index = filters.nodeTypes.indexOf(type)
  if (index > -1) {
    filters.nodeTypes.splice(index, 1)
  } else {
    filters.nodeTypes.push(type)
  }
}

// Handle click outside to close filter
function onGraphAreaClick(event) {
  const isFilterElement = event.target.closest('.floating-filter') || 
                         event.target.closest('.filter-trigger') ||
                         event.target.closest('.button-group') ||
                         event.target.closest('.field-input')
  
  if (!isFilterElement && showFilter.value) {
    showFilter.value = false
  }
}

function resetView() {
  if (!fg) return
  fg.zoomToFit(400, 50)
}

// Optimized: Simplified graph data construction
function buildGraphData(rawNodes, rawLinks) {
  const nodes = rawNodes.map(n => ({
    id: n.id,
    type: n.type,
    label: n.label,
    neighbors: [],
    links: [],
    degree: 0
  }))

  const nodeById = new Map()
  nodes.forEach(n => {
    nodeById.set(n.id, n)
  })

  const links = (rawLinks || [])
    .map(l => ({ source: l.source, target: l.target }))
    .filter(l => nodeById.has(l.source) && nodeById.has(l.target))

  links.forEach(l => {
    const a = nodeById.get(l.source)
    const b = nodeById.get(l.target)
    if (a && b) {
      a.neighbors.push(b)
      b.neighbors.push(a)
      a.links.push(l)
      b.links.push(l)
      a.degree++
      b.degree++
    }
  })

  return { nodes, links }
}

function optimizeGraphData(graphData) {
  console.log(`📊 Before optimization: ${graphData.nodes.length} nodes, ${graphData.links.length} links`)
  
  if (graphData.nodes.length > PERFORMANCE_CONFIG.MAX_NODES) {
    graphData.nodes = graphData.nodes
      .sort((a, b) => (b.links?.length || 0) - (a.links?.length || 0))
      .slice(0, PERFORMANCE_CONFIG.MAX_NODES)
    
    const nodeIds = new Set(graphData.nodes.map(n => n.id))
    graphData.links = graphData.links
      .filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))
      .slice(0, PERFORMANCE_CONFIG.MAX_LINKS)
  }
  
  console.log(`🎯 After optimization: ${graphData.nodes.length} nodes, ${graphData.links.length} links`)
  return graphData
}

function highlightConnectedNodes(node) {
  if (!node) {
    highlightNodes = new Set()
    highlightLinks = new Set()
    draggedNode = null
    return
  }

  const newNodes = new Set([node])
  const newLinks = new Set()
  
  node.links.forEach(l => newLinks.add(l))
  
  highlightNodes = newNodes
  highlightLinks = newLinks
  draggedNode = node
}

// Reset highlight
function clearHighlight() {
  highlightNodes = new Set()
  highlightLinks = new Set()
  draggedNode = null
}

onMounted(async () => {
  await nextTick()
  
  console.log('🔍 Check the initial layout:')
  if (graphWrapper.value) {
    const style = window.getComputedStyle(graphWrapper.value)
    console.log('graphWrapper Style:', {
      height: style.height,
      maxHeight: style.maxHeight,
      minHeight: style.minHeight,
      flex: style.flex,
      display: style.display
    })
  }
  
  const el = graphEl.value
  if (!el) {
    console.warn('graphEl not ready, retrying...')
    setTimeout(() => {
      if (graphEl.value) {
        initializeGraph()
      }
    }, 100)
    return
  }

  if (!ForceGraph) {
    console.error('ForceGraph module not available')
    return
  }

  initializeGraph()
})

async function initializeGraph() {
  if (!isDataLoaded.value) {
    await loadGraphData()
  }

  initForceGraph(graphEl.value)
  
  await nextTick()
  applyFilters()
  
  isGraphInitialized.value = true
}

// Optimized: Separate data loading logic
async function loadGraphData() {
  isLoading.value = true
  try {
    console.log('🚀 Starting graph data loading...')

    const data = await loadGraphDataPage(0, PERFORMANCE_CONFIG.MAX_NODES)
    
    if (!data.nodes || data.nodes.length === 0) {
      console.log('❌ No data received from API')
      rawGraphData.value = { nodes: [], links: [] }
      return
    }

    console.log(`📥 Raw data: ${data.nodes.length} nodes, ${data.links?.length || 0} links`)

    rawGraphData.value = { 
      nodes: data.nodes.slice(0, PERFORMANCE_CONFIG.MAX_NODES * 2), 
      links: data.links ? data.links.slice(0, PERFORMANCE_CONFIG.MAX_LINKS * 2) : [] 
    }
    
    fullGraphData = buildGraphData(rawGraphData.value.nodes, rawGraphData.value.links)
    fullGraphData = optimizeGraphData(fullGraphData)
    currentGraphData = fullGraphData

    if (filters.nodeTypes.length === 0) {
      filters.nodeTypes = [...availableNodeTypes.value]
    }
    
    isDataLoaded.value = true
    console.log('✅ Graph data loading completed')
    
  } catch (err) {
    console.error('❌ Failed to load graph data:', err)
    rawGraphData.value = { nodes: [], links: [] }
  } finally {
    isLoading.value = false
  }
}

// Load graph data by page
async function loadGraphDataPage(page, size) {
  try {
    const url = `http://localhost:8000/api/v1/sdkg/index?page=${page}&size=${size}&ts=${Date.now()}`
    const res = await fetch(url, { cache: 'no-store' })
    return await res.json()
  } catch (err) {
    console.error('Failed to load graph data page:', err)
    return { nodes: [], links: [] }
  }
}

function initForceGraph(el) {
  if (fg) {
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }

  const settings = {
    alphaMin: 0.001,
    alphaDecay: 0.0228,
    velocityDecay: 0.4,
    linkDistance: 50,
    chargeStrength: -80,
    centerStrength: 0.05,
    collideRadius: 8
  }

  try {
    fg = ForceGraph()(el)
      .graphData(currentGraphData || { nodes: [], links: [] })
      .backgroundColor('rgba(0,0,0,0)')
      .nodeId('id')
      .linkSource('source')
      .linkTarget('target')
      .d3AlphaMin(settings.alphaMin)
      .d3AlphaDecay(settings.alphaDecay)
      .d3VelocityDecay(settings.velocityDecay)
      .cooldownTicks(100)
      .warmupTicks(20)
      .enableNodeDrag(true)
      .linkColor(LINK_COLORS.default)
      .linkWidth(1.0)
      .nodeVal('degree')
      .nodeRelSize(0.5)
    
    configureForces(fg, settings)

    fg.nodeCanvasObjectMode(() => 'replace')
      .nodeCanvasObject((node, ctx, globalScale) => {
        if (globalScale < 0.3) return 
        
        const baseColor = TYPE_COLORS[node.type] || TYPE_COLORS.default
        const isHighlighted = highlightNodes.has(node)
        
        const baseRadius = PERFORMANCE_CONFIG.NODE_RADIUS
        const degree = node.degree || 1
        const radius = Math.min(
          baseRadius + Math.log2(degree + 1) * 0.8,
          8
        )
        
        const nodeRadius = isHighlighted ? radius * 1.3 : radius
        const nodeColor = isHighlighted ? '#fbbf24' : baseColor
        
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()

        if (globalScale > 5) {
          const label = node.label || node.id
          const fontSize = Math.min(32, 28 / globalScale)
          ctx.font = `${fontSize}px system-ui`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'top'
          ctx.fillStyle = isHighlighted ? '#92400e' : '#6b7280'
          ctx.fillText(label, node.x, node.y + nodeRadius + 1 / globalScale)
        }
      })
      .linkCanvasObjectMode(() => 'after')
      .linkCanvasObject((link, ctx) => {
        if (!fg || fg.zoom() < 0.5) return
        
        const isHighlighted = highlightLinks.has(link)
        
        ctx.beginPath()
        ctx.moveTo(link.source.x, link.source.y)
        ctx.lineTo(link.target.x, link.target.y)
        
        if (isHighlighted) {
          ctx.strokeStyle = LINK_COLORS.highlighted
          ctx.lineWidth = 2.0
          ctx.setLineDash([])
          
          ctx.shadowBlur = 5
          ctx.shadowColor = LINK_COLORS.highlighted
        } else {
          ctx.strokeStyle = LINK_COLORS.default
          ctx.lineWidth = 0.8
          ctx.setLineDash([])
          ctx.shadowBlur = 0
        }
        
        ctx.stroke()
        ctx.shadowBlur = 0
      })
      .nodePointerAreaPaint((node, color, ctx) => {
        const baseRadius = PERFORMANCE_CONFIG.NODE_RADIUS
        const degree = node.degree || 1
        const radius = Math.min(
          baseRadius + Math.log2(degree + 1) * 0.8,
          8
        ) + 0.5
        
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
        ctx.fillStyle = color
        ctx.fill()
      })
      .onNodeHover(debounce((node) => {
        if (draggedNode) return
        
        if (!node) {
          highlightNodes = new Set()
          highlightLinks = new Set()
          return
        }

        const newNodes = new Set([node])
        const newLinks = new Set()
        
        node.neighbors.slice(0, 5).forEach(n => newNodes.add(n)) 
        node.links.slice(0, 10).forEach(l => newLinks.add(l)) 
        
        highlightNodes = newNodes
        highlightLinks = newLinks
      }, 16)) 
      .onNodeDrag((node) => {
        highlightConnectedNodes(node)
      })
      .onNodeDragEnd(() => {
        clearHighlight()
      })
      .onNodeClick((node) => {
        router.push(`/node/${node.id}`)
      })

    let hasAutoZoomed = false
    fg.onEngineStop(() => {
      console.log('🔄 Force simulation stabilized')

      if (isFirstLoad.value && !hasAutoZoomed && fg) {
        hasAutoZoomed = true
        isFirstLoad.value = false

        setTimeout(() => {
          if (fg) {
            console.log('🎯 Performing initial auto-zoom')
            fg.zoomToFit(400, 50)

            fg.centerAt(0, 0, 1000)
          }
        }, 300)
      }
    })

    let isUpdating = false
    let lastUpdateTime = 0
    let lastWidth = 0
    let lastHeight = 0
    
    const updateGraphSize = () => {
      if (!graphWrapper.value || !fg || isUpdating) return
      
      isUpdating = true
      const rect = graphWrapper.value.getBoundingClientRect()
      const now = Date.now()

      if (Math.abs(rect.width - lastWidth) < 2 && Math.abs(rect.height - lastHeight) < 2) {
        isUpdating = false
        return
      }

      if (now - lastUpdateTime < 200) {
        isUpdating = false
        return
      }
      
      lastWidth = rect.width
      lastHeight = rect.height
      lastUpdateTime = now
      
      console.log('📏 Update ForceGraph Size:', rect.width.toFixed(0), 'x', rect.height.toFixed(0))
      fg.width(rect.width).height(rect.height)
      
      isUpdating = false
    }
    
    const debouncedUpdate = debounce(updateGraphSize, 250)
    
    const resizeObserver = new ResizeObserver(() => {
      if (!graphWrapper.value) return
      const rect = graphWrapper.value.getBoundingClientRect()
      console.log('📐 Vessel size change detected:', rect.width.toFixed(0), 'x', rect.height.toFixed(0))
      debouncedUpdate()
    })

    if (graphWrapper.value) {
      const rect = graphWrapper.value.getBoundingClientRect()
      lastWidth = rect.width
      lastHeight = rect.height
      lastUpdateTime = Date.now()
      fg.width(rect.width).height(rect.height)
      
      resizeObserver.observe(graphWrapper.value)
      fg._resizeObserver = resizeObserver
    }

    console.log('✅ ForceGraph initialized')
    
  } catch (error) {
    console.error('❌ Failed to initialize ForceGraph:', error)
  }
}

function configureForces(graphInstance, settings) {
  try {
    const linkForce = graphInstance.d3Force('link')
    if (linkForce && typeof linkForce.distance === 'function') {
      linkForce.distance(settings.linkDistance || 50)
      if (typeof linkForce.strength === 'function') {
        linkForce.strength(0.1)
      }
    }

    const chargeForce = graphInstance.d3Force('charge')
    if (chargeForce && typeof chargeForce.strength === 'function') {
      chargeForce.strength(settings.chargeStrength || -80)
      if (typeof chargeForce.distanceMax === 'function') {
        chargeForce.distanceMax(200)
      }
    }

    const centerForce = graphInstance.d3Force('center')
    if (centerForce && typeof centerForce.strength === 'function') {
      centerForce.strength(settings.centerStrength || 0.05)
    }

    console.log('✅ Forces configured with:', settings)
    
  } catch (error) {
    console.warn('Force configuration warning:', error.message)
  }
}

onBeforeUnmount(() => {
  if (fg) {
    if (fg._resizeObserver) {
      fg._resizeObserver.disconnect()
      fg._resizeObserver = null
    }
    
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }
})

let filterTimeout = null
function applyFilters() {
  if (filterTimeout) {
    clearTimeout(filterTimeout)
  }
  
  filterTimeout = setTimeout(() => {
    if (!fg || !rawGraphData.value.nodes) return

    console.time('Filtering performance')
    const filteredData = performFiltering()
    currentGraphData = optimizeGraphData(filteredData)

    fg.graphData(currentGraphData)

    setTimeout(() => {
      if (fg) {
        configureForces(fg, {
          alphaMin: 0.001,
          alphaDecay: 0.0228,
          velocityDecay: 0.4,
          linkDistance: 50,
          chargeStrength: -80,
          centerStrength: 0.05
        })

        setTimeout(() => {
          if (fg) {
            fg.zoomToFit(400, 50)
          }
        }, 800)
      }
    }, 100)
    
    clearHighlight()
    console.timeEnd('Filtering performance')
  }, 100)
}

function performFiltering() {
  const keyword = filters.keyword.trim().toLowerCase()
  const selectedNodeTypes = filters.nodeTypes

  let filteredNodesRaw = rawGraphData.value.nodes.filter(n => {
    if (selectedNodeTypes.length > 0 && !selectedNodeTypes.includes(n.type)) {
      return false
    }

    if (keyword) {
      const text = `${n.label || ''} ${n.id}`.toLowerCase()
      if (!text.includes(keyword)) return false
    }

    return true
  })

  const allowedIds = new Set(filteredNodesRaw.map(n => n.id))

  const filteredLinksRaw = rawGraphData.value.links.filter(l => 
    allowedIds.has(l.source) && allowedIds.has(l.target)
  )

  return buildGraphData(filteredNodesRaw, filteredLinksRaw)
}

// Reset all filters
function resetFilters() {
  filters.keyword = ''
  filters.nodeTypes = [...availableNodeTypes.value]

  if (!fg || !fullGraphData) return
  currentGraphData = fullGraphData
  fg.graphData(currentGraphData)
  
  setTimeout(() => {
    if (fg) {
      fg.zoomToFit(400, 50)
    }
  }, 800)
  
  clearHighlight()
}
</script>

<style scoped>
.loading-indicator {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.panel {
  flex: 1;
  flex-direction: column;
  width: 100%;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e5e5e5, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
}

.panel-header {
  padding: 18px 22px 10px 22px;
  border-bottom: 1px solid #e5e7eb;
}

.section-title {
  font-size: 34px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
}

.panel-body {
  flex: 1;
  flex-direction: column;
  padding: 3.5px 5.5px 4.5px 5.5px;
  box-sizing: border-box;
  background: #f9fafb;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.graph-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  min-height: 400px;
  height: 100%;
  min-height: 0;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  display: block;
  position: absolute;
  top: 0;
  left: 0;
}

.field {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 30px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #e5e7eb;
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.7);
  background: rgba(15, 23, 42, 0.9);
  padding: 20px 12px;
  font-size: 22px;
  color: #e5e7eb;
  outline: none;
  transition: all 0.2s ease;
}

.field-input::placeholder {
  color: #6b7280;
}

.field-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.8);
}

/* Enhanced button group styles */
.button-group {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.type-button {
  position: relative;
  padding: 14px 54px;
  border-radius: 8px;
  border: 1.5px solid rgba(148, 163, 184, 0.3);
  background: rgba(31, 41, 55, 0.8);
  color: #e5e7eb;
  font-size: 26px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-height: 44px;
  justify-content: center;
}

.type-button:hover {
  background: rgba(55, 65, 81, 0.9);
  border-color: rgba(148, 163, 184, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.type-button-active {
  background: rgba(37, 99, 235, 0.2);
  border-color: var(--type-color, #3b82f6);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.type-button-active:hover {
  background: rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
}

.button-text {
  font-weight: 500;
  letter-spacing: 0.02em;
}


/* Responsive adjustments */
@media (max-width: 768px) {
  .button-group {
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }
  
  .type-button {
    padding: 8px 4px;
    min-height: 40px;
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .button-group {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>