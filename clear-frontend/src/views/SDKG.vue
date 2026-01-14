<template>
  <AppPageLayout>
    <section class="panel">
      <!-- Enhanced header with decorative elements and gradient background -->
      <header class="panel-header">
        <!-- Decorative background elements -->
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
        
        <div class="title-container">
          <!-- Main title with gradient effect in a single line -->
          <h1 class="title">
            Structured Data-derived <span class="gradient-text">Knowledge Graph</span>
          </h1>
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

          <!-- Right details sidebar with resizable and draggable capabilities -->
          <div 
            ref="sidebarRef"
            class="details-sidebar" 
            :class="{ 'details-sidebar--visible': showDetailsSidebar }"
            :style="sidebarStyle"
            @mousedown="onSidebarDragStart"
          >
            <!-- Resize handle for left side -->
            <div 
              class="sidebar-resize-handle sidebar-resize-handle--left"
              @mousedown.stop="onResizeStart('left', $event)"
            ></div>
            
            <!-- Resize handle for top side -->
            <div 
              class="sidebar-resize-handle sidebar-resize-handle--top"
              @mousedown.stop="onResizeStart('top', $event)"
            ></div>
            
            <!-- Resize handle for top-left corner -->
            <div 
              class="sidebar-resize-handle sidebar-resize-handle--top-left"
              @mousedown.stop="onResizeStart('top-left', $event)"
            ></div>
            
            <div class="details-sidebar-header">
              <h3 class="details-title">Node Details</h3>
              <button class="sidebar-close-btn" @click="closeDetailsSidebar">
                <span>×</span>
              </button>
            </div>
            
            <div class="details-sidebar-content">
              <div v-if="showDebugInfo && currentNodeId" class="current-segment-info">
                <p>Loading details for node: <strong>{{ currentNodeId }}</strong></p>
                <p>URL: {{ detailPageUrl }}</p>
              </div>
              
              <div v-if="currentNodeId" class="node-details">
                <iframe 
                  :src="detailPageUrl"
                  class="details-iframe"
                  frameborder="0"
                  @load="onIframeLoad"
                  @error="onIframeError"
                  ref="detailsIframe"
                ></iframe>

                <div v-if="iframeLoading" class="iframe-loading-overlay">
                  <span class="loading-spinner"></span>
                  Loading page...
                </div>
              </div>

              <div v-else class="no-details">
                Click a node to view details
              </div>
            </div>

            <div class="details-sidebar-footer">
              <!-- Open full page button -->
              <button 
                class="open-full-btn"
                @click="openDetailsInCurrentTab"
                :disabled="!currentNodeId"
              >
                Open
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import ForceGraphModule from 'force-graph'

import AppPageLayout from '../components/AppPageLayout.vue'
import FloatingFilter from '../components/FloatingFilter.vue'

const ForceGraph = ForceGraphModule.default || ForceGraphModule

const graphEl = ref(null)
const graphWrapper = ref(null)
const detailsIframe = ref(null) 
const sidebarRef = ref(null)
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

const showDetailsSidebar = ref(false)
const currentNodeId = ref(null)
const iframeLoading = ref(false) 
const detailError = ref(null)
const showDebugInfo = ref(false) 
let loadTimeout = null 

// Filter UI state
const showFilter = ref(false)

// Filter conditions
const filters = reactive({
  keyword: '',
  nodeTypes: []
})

// Sidebar resize and drag state
const sidebarPosition = reactive({
  x: 0, // Horizontal position from right
  y: 0, // Vertical position from top
  width: 400, // Default width
  height: '100%' // Default height (percentage or px)
})

// Store original sidebar position for resetting
const originalSidebarPosition = {
  x: 0,
  y: 0,
  width: 400,
  height: '100%'
}

const isResizing = ref(false)
const resizeDirection = ref(null)
const isDragging = ref(false)
const dragStartPos = reactive({ x: 0, y: 0 })

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
  behavior: '#3b82f6',        
  attribute: '#0ea5e9',     
  function: '#06b6d4',      
  segment: '#6366f1',       
  trajectory: '#8b5cf6',    
  default: '#64748b'        
}

// Enhanced link colors for better visual appeal
const LINK_COLORS = {
  default: {
    primary: 'rgba(59, 130, 246, 0.15)',
    secondary: 'rgba(139, 92, 246, 0.1)',
    accent: 'rgba(99, 102, 241, 0.08)'
  },
  highlighted: {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    glow: 'rgba(59, 130, 246, 0.3)'
  }
}

const HIGHLIGHT_COLORS = {
  link: '#fbbf24'
}

// Computed properties
const availableNodeTypes = computed(() => {
  const types = new Set()
  rawGraphData.value.nodes?.forEach(n => {
    if (n.type) types.add(n.type)
  })
  return Array.from(types).sort().slice(0, 5)
})

// Computed property for sidebar style - FIXED
const sidebarStyle = computed(() => {
  if (!showDetailsSidebar.value) {
    // When sidebar is hidden, position it completely off-screen
    return {
      right: '-1000px', // Move it far off-screen
      transform: 'none',
      width: '0',
      height: '0',
      opacity: '0',
      visibility: 'hidden'
    }
  } else {
    // When sidebar is visible, use its current position and size
    const baseStyle = {
      width: typeof sidebarPosition.width === 'number' ? `${sidebarPosition.width}px` : sidebarPosition.width,
      height: sidebarPosition.height,
      transform: `translate(${sidebarPosition.x}px, ${sidebarPosition.y}px)`,
      right: '0',
      opacity: '1',
      visibility: 'visible'
    }
    
    return baseStyle
  }
})

const detailPageUrl = computed(() => {
  if (!currentNodeId.value) return ''
  return `/node/${currentNodeId.value}?embed=true`
})

/**
 * Open the details sidebar for a specific node
 * @param {string} nodeId - ID of the node to display
 */
const openDetailsSidebar = (nodeId) => {
  console.log('Opening details sidebar for node:', nodeId)

  detailError.value = null
  currentNodeId.value = nodeId

  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }

  // Reset sidebar position to default if it was previously moved/resized
  if (sidebarPosition.x !== originalSidebarPosition.x || 
      sidebarPosition.y !== originalSidebarPosition.y ||
      sidebarPosition.width !== originalSidebarPosition.width) {
    resetSidebarPosition()
  }

  showDetailsSidebar.value = true

  nextTick(() => {
    // Show loading state for iframe
    iframeLoading.value = true

    // Set timeout for iframe loading
    loadTimeout = setTimeout(() => {
      if (iframeLoading.value) {
        console.warn('Iframe loading timeout for:', detailPageUrl.value)
        detailError.value = 'Page loading timeout. The page may not exist or is taking too long to load.'
        iframeLoading.value = false
      }
    }, 8000)
  })
}

/**
 * Close the details sidebar and reset its position
 */
const closeDetailsSidebar = () => {
  showDetailsSidebar.value = false
  currentNodeId.value = null
  detailError.value = null
  iframeLoading.value = false

  // Reset sidebar position to default
  resetSidebarPosition()

  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
}

/**
 * Reset sidebar position to its original/default values
 */
const resetSidebarPosition = () => {
  sidebarPosition.x = originalSidebarPosition.x
  sidebarPosition.y = originalSidebarPosition.y
  sidebarPosition.width = originalSidebarPosition.width
  sidebarPosition.height = originalSidebarPosition.height
}

/**
 * Open the details page in the current browser tab
 */
const openDetailsInCurrentTab = () => {
  if (currentNodeId.value) {
    window.location.href = `/node/${currentNodeId.value}`
  }
}

/**
 * Handle iframe load event
 * @param {Event} event - Load event
 */
const onIframeLoad = (event) => {
  console.log('Details page loaded successfully:', detailPageUrl.value)
  iframeLoading.value = false
  detailError.value = null

  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
}

/**
 * Handle iframe error event
 * @param {Event} event - Error event
 */
const onIframeError = (event) => {
  console.error('Failed to load details page:', detailPageUrl.value)
  console.error('Iframe error event:', event)
  detailError.value = `Failed to load page: ${detailPageUrl.value}`
  iframeLoading.value = false

  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
}

/**
 * Start resizing the sidebar
 * @param {string} direction - Resize direction (left, top, top-left)
 * @param {MouseEvent} event - Mouse event
 */
const onResizeStart = (direction, event) => {
  event.preventDefault()
  isResizing.value = true
  resizeDirection.value = direction
  dragStartPos.x = event.clientX
  dragStartPos.y = event.clientY
  
  const startWidth = sidebarPosition.width
  const startHeight = sidebarPosition.height === '100%' 
    ? sidebarRef.value.parentElement.clientHeight 
    : parseInt(sidebarPosition.height)
  const startX = sidebarPosition.x
  const startY = sidebarPosition.y
  
  const handleMouseMove = (e) => {
    if (!isResizing.value) return
    
    const dx = e.clientX - dragStartPos.x
    const dy = e.clientY - dragStartPos.y
    
    if (direction.includes('left')) {
      const newWidth = Math.max(300, Math.min(800, startWidth - dx))
      sidebarPosition.width = newWidth
    }
    
    if (direction.includes('top')) {
      const newHeight = Math.max(200, Math.min(window.innerHeight - 100, startHeight - dy))
      sidebarPosition.height = `${newHeight}px`
      sidebarPosition.y = startY + dy
    }
  }
  
  const handleMouseUp = () => {
    isResizing.value = false
    resizeDirection.value = null
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

/**
 * Start dragging the sidebar
 * @param {MouseEvent} event - Mouse event
 */
const onSidebarDragStart = (event) => {
  // Only start drag if clicking on the header
  if (!event.target.closest('.details-sidebar-header')) return
  
  event.preventDefault()
  isDragging.value = true
  dragStartPos.x = event.clientX - sidebarPosition.x
  dragStartPos.y = event.clientY - sidebarPosition.y
  
  const handleMouseMove = (e) => {
    if (!isDragging.value) return
    
    const mapWrapper = sidebarRef.value.parentElement
    const maxX = mapWrapper.clientWidth - sidebarPosition.width
    const maxY = mapWrapper.clientHeight - parseInt(sidebarPosition.height)
    
    let newX = e.clientX - dragStartPos.x
    let newY = e.clientY - dragStartPos.y
    
    // Constrain to parent bounds
    newX = Math.max(-sidebarPosition.width + 20, Math.min(maxX - 20, newX))
    newY = Math.max(0, Math.min(maxY, newY))
    
    sidebarPosition.x = newX
    sidebarPosition.y = newY
  }
  
  const handleMouseUp = () => {
    isDragging.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// Watch for changes to the detail page URL
watch(detailPageUrl, (newUrl, oldUrl) => {
  console.log('Iframe URL changed:', oldUrl, '->', newUrl)
  if (newUrl && newUrl !== oldUrl) {
    iframeLoading.value = true
  }
})

/**
 * Debounce function to limit rate of function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
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

/**
 * Handle click on graph area to close filter
 * @param {Event} event - Click event
 */
function onGraphAreaClick(event) {
  const isFilterElement = event.target.closest('.floating-filter') || 
                         event.target.closest('.filter-trigger') ||
                         event.target.closest('.button-group') ||
                         event.target.closest('.field-input')
  
  if (!isFilterElement && showFilter.value) {
    showFilter.value = false
  }
}

/**
 * Reset the graph view to fit all nodes
 */
function resetView() {
  if (!fg) return
  fg.zoomToFit(400, 50)
}

/**
 * Build graph data structure from raw nodes and links
 * @param {Array} rawNodes - Array of raw node objects
 * @param {Array} rawLinks - Array of raw link objects
 * @returns {Object} Processed graph data with nodes and links
 */
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

/**
 * Optimize graph data for performance by limiting number of nodes and links
 * @param {Object} graphData - Graph data object
 * @returns {Object} Optimized graph data
 */
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

/**
 * Highlight nodes connected to the specified node
 * @param {Object} node - Node to highlight connections for
 */
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

/**
 * Clear all highlight states
 */
function clearHighlight() {
  highlightNodes = new Set()
  highlightLinks = new Set()
  draggedNode = null
}

/**
 * Component mounted lifecycle hook
 */
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

/**
 * Initialize the force graph visualization
 */
async function initializeGraph() {
  if (!isDataLoaded.value) {
    await loadGraphData()
  }

  initForceGraph(graphEl.value)
  
  await nextTick()
  applyFilters()
  
  isGraphInitialized.value = true
}

/**
 * Load graph data from the API
 */
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

/**
 * Load a page of graph data from the API
 * @param {number} page - Page number
 * @param {number} size - Page size
 * @returns {Promise<Object>} Graph data object
 */
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

/**
 * Initialize the ForceGraph instance
 * @param {HTMLElement} el - DOM element to render graph in
 */
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
      .backgroundColor('rgba(0,0,0,0)') // Transparent background
      .nodeId('id')
      .linkSource('source')
      .linkTarget('target')
      .d3AlphaMin(settings.alphaMin)
      .d3AlphaDecay(settings.alphaDecay)
      .d3VelocityDecay(settings.velocityDecay)
      .cooldownTicks(100)
      .warmupTicks(20)
      .enableNodeDrag(true)
      .linkWidth(1.0)
      .nodeVal('degree')
      .nodeRelSize(0.5)
    
    configureForces(fg, settings)

    // Configure node rendering
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
        
        // Draw node with shadow for depth effect
        ctx.shadowColor = isHighlighted ? nodeColor : 'rgba(0, 0, 0, 0.2)'
        ctx.shadowBlur = isHighlighted ? 15 : 5
        ctx.shadowOffsetX = 0
        ctx.shadowOffsetY = 0
        
        ctx.beginPath()
        ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()
        
        // Reset shadow
        ctx.shadowBlur = 0
        
        // Add inner glow for highlighted nodes
        if (isHighlighted) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, nodeRadius * 0.6, 0, 2 * Math.PI, false)
          ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
          ctx.fill()
        }

        // Render node label if zoomed in
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
      .linkCanvasObject((link, ctx, globalScale) => {
        if (!fg || globalScale < 0.3) return
        
        const isHighlighted = highlightLinks.has(link)
        const sourceNode = link.source
        const targetNode = link.target
        
        // Skip if nodes are not properly positioned
        if (!sourceNode || !targetNode || !sourceNode.x || !targetNode.x) return
        
        // Calculate link properties
        const dx = targetNode.x - sourceNode.x
        const dy = targetNode.y - sourceNode.y
        const length = Math.sqrt(dx * dx + dy * dy)
        const unitX = dx / length
        const unitY = dy / length
        
        // Enhanced link rendering with gradient and glow effects
        if (isHighlighted) {
          // Create gradient for highlighted links
          const gradient = ctx.createLinearGradient(
            sourceNode.x, sourceNode.y,
            targetNode.x, targetNode.y
          )
          gradient.addColorStop(0, LINK_COLORS.highlighted.primary)
          gradient.addColorStop(0.5, LINK_COLORS.highlighted.secondary)
          gradient.addColorStop(1, LINK_COLORS.highlighted.primary)
          
          // Draw outer glow
          ctx.beginPath()
          ctx.moveTo(sourceNode.x, sourceNode.y)
          ctx.lineTo(targetNode.x, targetNode.y)
          ctx.strokeStyle = LINK_COLORS.highlighted.glow
          ctx.lineWidth = 6
          ctx.lineCap = 'round'
          ctx.shadowBlur = 10
          ctx.shadowColor = LINK_COLORS.highlighted.primary
          ctx.stroke()
          
          // Draw main link with gradient
          ctx.beginPath()
          ctx.moveTo(sourceNode.x, sourceNode.y)
          ctx.lineTo(targetNode.x, targetNode.y)
          ctx.strokeStyle = gradient
          ctx.lineWidth = 3
          ctx.lineCap = 'round'
          ctx.shadowBlur = 8
          ctx.stroke()
          
          // Reset shadow
          ctx.shadowBlur = 0
          
          // Add animated pulse effect for active links
          if (globalScale > 1) {
            const pulseSize = 4 * Math.sin(Date.now() * 0.005)
            if (pulseSize > 0) {
              // Draw pulse circle at midpoint
              const midX = (sourceNode.x + targetNode.x) / 2
              const midY = (sourceNode.y + targetNode.y) / 2
              
              ctx.beginPath()
              ctx.arc(midX, midY, pulseSize, 0, 2 * Math.PI)
              ctx.fillStyle = LINK_COLORS.highlighted.primary
              ctx.fill()
            }
          }
        } else {
          // Create gradient for normal links
          const gradient = ctx.createLinearGradient(
            sourceNode.x, sourceNode.y,
            targetNode.x, targetNode.y
          )
          gradient.addColorStop(0, LINK_COLORS.default.primary)
          gradient.addColorStop(0.5, LINK_COLORS.default.secondary)
          gradient.addColorStop(1, LINK_COLORS.default.accent)
          
          // Draw normal link with subtle gradient
          ctx.beginPath()
          ctx.moveTo(sourceNode.x, sourceNode.y)
          ctx.lineTo(targetNode.x, targetNode.y)
          ctx.strokeStyle = gradient
          ctx.lineWidth = Math.max(0.5, Math.min(1.5, 1.5 / globalScale))
          ctx.lineCap = 'round'
          ctx.stroke()
          
          // Add subtle glow effect for normal links
          if (globalScale > 2) {
            ctx.beginPath()
            ctx.moveTo(sourceNode.x, sourceNode.y)
            ctx.lineTo(targetNode.x, targetNode.y)
            ctx.strokeStyle = 'rgba(59, 130, 246, 0.05)'
            ctx.lineWidth = Math.max(2, 4 / globalScale)
            ctx.stroke()
          }
        }
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
        // Only highlight nodes during drag, do not open sidebar
        highlightConnectedNodes(node)
      })
      .onNodeDragEnd(() => {
        clearHighlight()
      })
      .onNodeClick((node) => {
        // On click, open the details sidebar instead of navigating to a new page
        openDetailsSidebar(node.id)
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

    // Set up responsive resizing
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

/**
 * Configure physics forces for the graph
 * @param {Object} graphInstance - ForceGraph instance
 * @param {Object} settings - Physics settings
 */
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

/**
 * Component before unmount lifecycle hook
 */
onBeforeUnmount(() => {
  if (fg) {
    if (fg._resizeObserver) {
      fg._resizeObserver.disconnect()
      fg._resizeObserver = null
    }
    
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }

  if (loadTimeout) {
    clearTimeout(loadTimeout)
  }
})

let filterTimeout = null

/**
 * Apply current filters to the graph
 */
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

/**
 * Perform filtering based on current filter criteria
 * @returns {Object} Filtered graph data
 */
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

/**
 * Reset all filters to their default values
 */
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

/* Main panel container with improved visual hierarchy */
.panel {
  flex: 1;
  flex-direction: column;
  width: 100%;
  border-radius: 16px; /* Modern rounded corners */
  background: #ffffff; /* Clean white background */
  box-shadow: 0 0 0 1px rgba(226, 232, 240, 0.8), 0 20px 40px rgba(15, 23, 42, 0.1); /* Softer shadow */
  display: flex;
  overflow: hidden; /* Ensure content stays within rounded corners */
}

/* Enhanced panel header with gradient background and decorative elements */
.panel-header {
  padding: 2.5rem 2rem 1.5rem 2rem; /* Generous padding */
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); /* Subtle gradient background */
  border-bottom: 1px solid #e2e8f0; /* Soft border color */
  position: relative;
  overflow: hidden;
}

/* Decorative background elements for visual interest */
.header-decoration {
  position: absolute;
  top: -100px;
  right: -100px;
  z-index: 1;
  pointer-events: none;
}

.decoration-circle {
  border-radius: 50%;
  position: absolute;
  opacity: 0.6;
}

.circle-1 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
  top: 0;
  right: 0;
}

.circle-2 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  top: 40px;
  right: 40px;
}

.circle-3 {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
  top: 80px;
  right: 80px;
}

/* Title container with left-aligned text and improved typography */
.title-container {
  position: relative;
  z-index: 2;
  text-align: left; /* Ensure left alignment */
  width: 100%; /* Full width for left alignment */
}

/* Main title with consistent font size and gradient effect */
.title {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem; /* Consistent with other pages */
  font-weight: 700; /* Bold weight */
  line-height: 1.2;
  color: #1e293b; /* Dark color for good contrast */
  letter-spacing: -0.5px; /* Slightly tighter letter spacing */
}

/* Gradient text effect matching homepage hero title */
.gradient-text {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700; /* Bold weight for gradient text */
}

/* Subtitle with improved readability */
.subtitle {
  margin: 0;
  font-size: 1.125rem; /* Larger for better readability */
  line-height: 1.6;
  color: #475569; /* Softer gray color */
  max-width: 800px; /* Limit width for readability */
}

/* MODIFIED: Enhanced panel body with better background */
.panel-body {
  flex: 1;
  flex-direction: column;
  padding: 1.5rem; /* Increased padding for better spacing */
  box-sizing: border-box;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); /* Gradient background matching homepage */
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* MODIFIED: Enhanced graph wrapper with sophisticated background */
.graph-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  border-radius: 12px; /* Slightly larger radius */
  border: 1px solid rgba(226, 232, 240, 0.8); /* Softer border */
  background: linear-gradient(135deg, #e0f2fe 0%, #ede9fe 100%); /* Sophisticated gradient background */
  box-shadow: 
    0 4px 20px rgba(15, 23, 42, 0.08), /* Soft shadow */
    inset 0 1px 2px rgba(255, 255, 255, 0.8); /* Inner light for depth */
  overflow: hidden;
  min-height: 500px; /* Increased minimum height */
  height: 100%;
  min-height: 0;
}

/* Add subtle pattern overlay for visual interest */
.graph-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(59, 130, 246, 0.02) 1px, transparent 1px),
    radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  opacity: 0.5;
  pointer-events: none;
  z-index: 0;
}

.graph-canvas {
  width: 100%;
  height: 100%;
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1; /* Ensure canvas is above the background pattern */
}

.details-sidebar {
  position: absolute;
  top: 16px;
  right: 16px;
  bottom: 16px;
  background: white;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1); /* Enhanced shadow */
  z-index: 100;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* Smoother transition */
  border-left: 1px solid #e2e8f0;
  border-radius: 12px 0 0 12px; /* Larger radius */
  cursor: default;
  user-select: none;
  will-change: transform, right, opacity, visibility;
}

/* IMPORTANT FIX: Make sure sidebar is completely hidden when not visible */
.details-sidebar:not(.details-sidebar--visible) {
  right: -1000px !important;
  transform: none !important;
  width: 0 !important;
  height: 0 !important;
  opacity: 0 !important;
  visibility: hidden !important;
  pointer-events: none !important;
}

.details-sidebar--visible {
  right: 16px;
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}

.details-sidebar-header {
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
  border-radius: 12px 0 0 0;
}

.details-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.sidebar-close-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px; /* Larger radius */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  font-size: 24px;
  line-height: 1;
  padding: 0;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.sidebar-close-btn:hover {
  background: #f1f5f9;
  color: #475569;
}

.details-sidebar-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.current-segment-info {
  padding: 12px 20px;
  background: #fef3c7;
  border-bottom: 1px solid #fbbf24;
  font-size: 12px;
  color: #92400e;
}

.current-segment-info p {
  margin: 4px 0;
}

.node-details {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}

.details-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
  flex: 1;
  border-radius: 0 0 0 12px; /* Rounded bottom corners */
}

.iframe-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 14px;
  gap: 12px;
  z-index: 10;
  border-radius: 0 0 0 12px; /* Match iframe radius */
}

.iframe-loading-overlay .loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.no-details {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
  font-style: normal;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.no-details::before {
  content: '📊';
  font-size: 32px;
  opacity: 0.5;
}

.details-sidebar-footer {
  padding: 18px 20px;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 0 0 0 12px;
}

.open-full-btn {
  width: 100%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); /* Gradient button */
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.open-full-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
}

.open-full-btn:active:not(:disabled) {
  transform: translateY(0);
}

.open-full-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

/* Resize handles */
.sidebar-resize-handle {
  position: absolute;
  background: transparent;
  z-index: 101;
}

.sidebar-resize-handle--left {
  left: -4px;
  top: 0;
  bottom: 0;
  width: 8px;
  cursor: ew-resize;
}

.sidebar-resize-handle--top {
  top: -4px;
  left: 0;
  right: 0;
  height: 8px;
  cursor: ns-resize;
}

.sidebar-resize-handle--top-left {
  top: -8px;
  left: -8px;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
}

/* Visual indicators for resize handles - only show when sidebar is visible */
.details-sidebar--visible .sidebar-resize-handle--left:hover,
.details-sidebar--visible .sidebar-resize-handle--left:active {
  background: rgba(59, 130, 246, 0.2);
}

.details-sidebar--visible .sidebar-resize-handle--top:hover,
.details-sidebar--visible .sidebar-resize-handle--top:active {
  background: rgba(59, 130, 246, 0.2);
}

.details-sidebar--visible .sidebar-resize-handle--top-left:hover,
.details-sidebar--visible .sidebar-resize-handle--top-left:active {
  background: rgba(59, 130, 246, 0.3);
}

.field {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #475569; /* Better contrast */
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  padding: 10px 12px;
  font-size: 14px;
  color: #1e293b;
  outline: none;
  transition: all 0.2s ease;
}

.field-input::placeholder {
  color: #94a3b8;
}

.field-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Enhanced button group styles */
.button-group {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.type-button {
  position: relative;
  padding: 10px 6px;
  border-radius: 8px;
  border: 1.5px solid rgba(203, 213, 225, 0.5);
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
  font-size: 12px;
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
  backdrop-filter: blur(10px); /* Glass effect */
}

.type-button:hover {
  background: rgba(241, 245, 249, 0.9);
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.type-button-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-color: var(--type-color, #3b82f6);
  color: var(--type-color, #3b82f6);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.type-button-active:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.25);
}

.button-text {
  font-weight: 500;
  letter-spacing: 0.02em;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .title {
    font-size: 2rem; /* Slightly smaller on tablets */
  }
  
  .subtitle {
    font-size: 1rem; /* Adjust subtitle size */
  }
  
  .graph-wrapper {
    min-height: 400px; /* Adjust minimum height */
  }
  
  .panel-header {
    padding: 2rem 1.5rem 1.25rem 1.5rem; /* Adjust padding */
  }
}

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
  
  .title {
    font-size: 1.75rem; /* Smaller for mobile */
  }
  
  .subtitle {
    font-size: 0.875rem; /* Smaller subtitle */
  }
  
  .panel-header {
    padding: 1.5rem 1rem 1rem 1rem; /* Compact padding */
  }
  
  .panel-body {
    padding: 1rem; /* Compact padding */
  }
  
  /* Adjust decoration circles for mobile */
  .header-decoration {
    top: -80px;
    right: -80px;
  }
  
  .circle-1 {
    width: 160px;
    height: 160px;
  }
  
  .circle-2 {
    width: 120px;
    height: 120px;
    top: 30px;
    right: 30px;
  }
  
  .circle-3 {
    width: 80px;
    height: 80px;
    top: 60px;
    right: 60px;
  }
}

@media (max-width: 480px) {
  .button-group {
    grid-template-columns: repeat(2, 1fr); /* Two columns on very small screens */
  }
  
  .title {
    font-size: 1.5rem; /* Even smaller for very small screens */
  }
  
  .subtitle {
    font-size: 0.75rem; /* Very small subtitle */
  }
  
  .details-sidebar {
    width: 100% !important;
    height: 50% !important;
    right: 0 !important;
    top: auto !important;
    bottom: 0 !important;
    border-radius: 12px 12px 0 0;
    border-left: none;
    border-top: 1px solid #e2e8f0;
  }
}
</style>