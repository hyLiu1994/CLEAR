<template>
  <div class="page-container">
    <div class="main-content">
      <!-- Title & meta area -->
      <header class="title-block">
        <h1 class="title">
          {{ node.title }}
        </h1>
      </header>

      <!-- Main content -->
      <section class="body">
        <div v-if="isFunctionType">
          <!-- Function Description -->
          <div v-if="functionDescription" class="function-section">
            <h2 class="section-title">Function Description</h2>
            <div class="function-description-plain">
              {{ functionDescription }}
            </div>
          </div>

          <!-- Code Implementation-->
          <div v-if="codeImplementation" class="code-section">
            <h2 class="section-title">Code Implementation</h2>
            <pre ref="codeBlock" class="code-plain">
              <code :class="'language-' + (detectedLanguage || 'python')">
                {{ codeImplementation }}
              </code>
            </pre>
          </div>
        </div>

        <template v-else>
          <h2 class="section-title">Description</h2>
          <!-- static attribute type special content -->
          <div v-if="isAttributeType && node.description" class="attribute-header">
            <div class="attribute-summary">
              <div class="attribute-summary-item">
                <strong>1. What is the definition of "Under way using engine"?</strong>
                <p>{{ attributeDefinition }}</p>
              </div>
              <div class="attribute-summary-item">
                <strong>2. What does the statistical information indicate?</strong>
                <div class="statistics-content">
                  <p>{{ attributeStatistics }}</p>
                  <div class="behavior-associations" v-if="topBehavior">
                    <div class="top-behavior">
                      <span class="label">Most associated behavior:</span>
                      <span class="value">{{ topBehavior.id }}</span>
                    </div>
                    <div class="association-count">
                      <span class="label">Associated behavior patterns:</span>
                      <span class="value">{{ behaviorAssociationCount }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <ul class="description-list">
            <li 
              v-for="(para, idx) in node.description" 
              :key="'p-' + idx"
              class="description-item"
            >
              <!-- main description content -->
              <div class="main-description">
                <template v-if="para.includes(':')">
                  <strong>{{ getSimpleTitle(para) }}:</strong>
                  <span class="description-text">
                    {{ getSimpleContent(para) }}
                  </span>
                </template>
                <template v-else>
                  {{ para }}
                </template>
              </div>
            </li>
          </ul>

          <!-- detailed descriptions -->
          <div v-if="hasDetailedDescriptions" class="detailed-section">
            <h2 class="section-title detailed-section-title">Detailed Explanations</h2>
            <div class="detailed-descriptions-container">
              <div 
                v-for="(detail, idx) in detailedDescriptions" 
                :key="'detail-' + idx"
                class="detailed-description-item"
              >
                <div class="detailed-item-header">
                  <span class="detail-index">{{ idx + 1 }}.</span>
                  <strong class="detailed-item-title">
                    {{ detail.title || `Detail ${idx + 1}` }}
                  </strong>
                </div>
                <div class="detailed-item-content">
                  <span class="detailed-text">{{ detail.content }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <template v-if="node.behavior && node.behavior.length">
          <h2 class="section-title">Behavioral patterns</h2>
          <ul class="bullet-list">
            <li v-for="(b, idx) in node.behavior" :key="'b-' + idx">
              {{ b }}
            </li>
          </ul>
        </template>

        <template v-if="node.notes && node.notes.length">
          <h2 class="section-title">Notes for analysts</h2>
          <ul class="bullet-list">
            <li v-for="(n, idx) in node.notes" :key="'n-' + idx">
              {{ n }}
            </li>
          </ul>
        </template>
      </section>
    </div>

    <div class="graph-sidebar" v-if="hasGraphData">
      <div class="graph-main-container">
        <section class="graph-section">
          <div class="graph-header">
            <div class="graph-title-row">
              <h3 class="graph-title">The Subgraph of SD-KG</h3>
              <button class="expand-btn" @click="expandGraph" title="Expand graph">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                </svg>
              </button>
            </div>
            
            <!-- Graph Controls -->
            <div class="graph-controls">

            </div>
          </div>
          
          <div class="graph-container">
            <div class="graph-wrapper" @click="onGraphAreaClick">
              <div ref="graphEl" class="graph-canvas"></div>
            </div>
          </div>
          
          <div class="graph-legend">
            <div class="legend-title">Node Types</div>
            <div class="legend-items">
              <div class="legend-item" v-for="type in nodeTypes" :key="type.name">
                <div class="legend-color" :style="{backgroundColor: type.color}"></div>
                <span class="legend-label">{{ type.label }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div v-if="isGraphExpanded" class="graph-modal" @click.self="closeExpandedGraph">
      <div class="graph-modal-content">
        <div class="graph-modal-header">
          <h3 class="graph-modal-title">{{ node.title }} - Knowledge Graph</h3>
          <button class="close-btn" @click="closeExpandedGraph" title="Close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="graph-modal-body">
          <div class="graph-modal-controls">

          </div>
          
          <div class="graph-modal-canvas-wrapper">
            <div ref="expandedGraphEl" class="graph-modal-canvas"></div>
          </div>
          
          <div class="graph-modal-legend">
            <div class="legend-title">Node Types</div>
            <div class="legend-items">
              <div class="legend-item" v-for="type in nodeTypes" :key="type.name">
                <div class="legend-color" :style="{backgroundColor: type.color}"></div>
                <span class="legend-label">{{ type.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch, onUpdated } from 'vue'
import ForceGraphModule from 'force-graph'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const ForceGraph = ForceGraphModule.default || ForceGraphModule

const props = defineProps({
  nodeId: {
    type: String,
    required: true
  },
  node: {
    type: Object,
    required: true
  },
  currentLevel: {
    type: Number,
    default: 2
  }
})

const isGraphExpanded = ref(false)
const expandedGraphEl = ref(null)
let expandedFg = null
const expandedCurrentLevel = ref(props.currentLevel)

let expandedHighlightNodes = new Set()
let expandedHighlightLinks = new Set()
let expandedDraggedNode = null

const isAttributeType = computed(() => props.node.type === 'attribute')
const isFunctionType = computed(() => props.node.type === 'function')

const functionDescription = computed(() => {
  if (!isFunctionType.value || !props.node.description) return ''
  
  const descriptionPara = props.node.description.find(para => {
    const colonIndex = para.indexOf(':')
    if (colonIndex === -1) return false
    const titlePart = para.substring(0, colonIndex).trim()
    return titlePart.toLowerCase().includes('function description')
  })
  
  if (descriptionPara) {
    const colonIndex = descriptionPara.indexOf(':')
    return descriptionPara.substring(colonIndex + 1).trim()
  }
  return ''
})

const codeImplementation = computed(() => {
  if (!isFunctionType.value || !props.node.description) return ''
  
  const codePara = props.node.description.find(para => {
    const colonIndex = para.indexOf(':')
    if (colonIndex === -1) return false
    const titlePart = para.substring(0, colonIndex).trim()
    return titlePart.toLowerCase().includes('code implementation')
  })
  
  if (codePara) {
    const colonIndex = codePara.indexOf(':')
    const codeContent = codePara.substring(colonIndex + 1).trim()

    const firstColonInCode = codeContent.indexOf(':')
    if (firstColonInCode !== -1) {
      const beforeColon = codeContent.substring(0, firstColonInCode + 1).trim()
      const afterColon = codeContent.substring(firstColonInCode + 1).trim()

      return `                          ${beforeColon}\n${afterColon}`
    }

    return ` ${codeContent}`
  }
  return ''
})

const detectedLanguage = ref('python')
const codeBlock = ref(null)

const detectLanguage = (code) => {
  if (!code) return 'python'
  
  const codeStr = code.toLowerCase()
  
  if (codeStr.includes('def ') || codeStr.includes('import ') || codeStr.includes('from ') || 
      codeStr.includes('print(') || codeStr.includes('class ') || codeStr.includes('self.')) {
    return 'python'
  } else if (codeStr.includes('function ') || codeStr.includes('const ') || codeStr.includes('let ') || 
             codeStr.includes('var ') || codeStr.includes('console.log') || codeStr.includes('export ')) {
    return 'javascript'
  } else if (codeStr.includes('select ') || codeStr.includes('from ') || codeStr.includes('where ') || 
             codeStr.includes('insert ') || codeStr.includes('update ')) {
    return 'sql'
  } else if (codeStr.includes('#include') || codeStr.includes('int main') || codeStr.includes('std::')) {
    return 'cpp'
  } else if (codeStr.includes('public class') || codeStr.includes('private ') || codeStr.includes('System.out.')) {
    return 'java'
  } else if (codeStr.includes('<?php') || codeStr.includes('echo ') || codeStr.includes('$')) {
    return 'php'
  } else if (codeStr.includes('func ') || codeStr.includes('package ') || codeStr.includes('import "')) {
    return 'go'
  }
  
  return 'python' 
}

const applyHighlight = () => {
  nextTick(() => {

    document.querySelectorAll('pre code').forEach((block) => {
      if (!block.classList.contains('hljs')) {
        const codeContent = block.textContent
        const language = detectLanguage(codeContent)
        block.className = `language-${language}`
        
        try {
          hljs.highlightElement(block)
        } catch (error) {
          console.warn('Code highlighting failed:', error)

          block.style.whiteSpace = 'pre-wrap'
          block.style.fontFamily = "'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace"
        }
      }
    })
  })
}

// Get the main title (remove the content in parentheses, but handle nested parentheses)
const getSimpleTitle = (text) => {
  const colonIndex = text.indexOf(':')
  if (colonIndex === -1) return text.trim()
  
  const titlePart = text.substring(0, colonIndex).trim()
  // Remove the entire content within parentheses (including nested ones)
  return titlePart.replace(/\([^()]*(?:\([^()]*\)[^()]*)*\)/g, '').trim()
}

// Extract the main content (remove the content in parentheses, but handle nested parentheses)
const getSimpleContent = (text) => {
  const colonIndex = text.indexOf(':')
  
  if (colonIndex === -1) {
    return text.replace(/\([^()]*(?:\([^()]*\)[^()]*)*\)/g, '').trim()
  }
  
  const contentPart = text.substring(colonIndex + 1).trim()
  return contentPart.replace(/\([^()]*(?:\([^()]*\)[^()]*)*\)/g, '').trim()
}

// Extract the detailed description within the parentheses
const getBracketContent = (text) => {
  const startBracket = text.indexOf('(')
  if (startBracket === -1) return null
  
  // Using a stack to handle nested parentheses
  let stack = 1
  let endBracket = -1
  
  for (let i = startBracket + 1; i < text.length; i++) {
    if (text[i] === '(') {
      stack++
    } else if (text[i] === ')') {
      stack--
      if (stack === 0) {
        endBracket = i
        break
      }
    }
  }
  
  if (endBracket !== -1 && endBracket > startBracket) {
    return text.substring(startBracket + 1, endBracket).trim()
  }
  return null
}

const attributeDefinition = computed(() => {
  if (props.node.description && props.node.description.length > 0) {
    const firstPara = props.node.description[0]
    if (firstPara.includes(':')) {
      const content = firstPara.split(':')[1]
      return content.trim().split('.')[0] + '.' 
    }
  }
  return "This attribute describes the vessel's operational status when it is underway and actively using its engine for propulsion, typically indicating normal navigation in progress."
})

const topBehavior = computed(() => {
  return {
    id: "behavior_28596560",
  }
})

const behaviorAssociationCount = computed(() => {
  return 12
})

const attributeStatistics = computed(() => {
  if (topBehavior.value) {
    return ``
  }
  return ``
})

const hasDetailedDescriptions = computed(() => {
  if (!props.node.description || isFunctionType.value) return false
  return props.node.description.some(para => getBracketContent(para))
})

const detailedDescriptions = computed(() => {
  if (!props.node.description || isFunctionType.value) return []
  
  return props.node.description
    .map((para, idx) => ({
      id: idx,
      title: getSimpleTitle(para),
      content: getBracketContent(para),
      originalText: para
    }))
    .filter(item => item.content)
})

// Graph references and state
const graphEl = ref(null)
let fg = null

// Performance configuration
const PERFORMANCE_CONFIG = {
  MAX_NODES: 1000,
  MAX_LINKS: 2000,
  NODE_RADIUS: 4,
  SIMULATION_QUALITY: 'medium'
}

const ANIMATION_CONFIG = {
  ALPHA_MIN: 0.001,
  ALPHA_DECAY: 0.02,        
  VELOCITY_DECAY: 0.6,       
  LINK_DISTANCE: 60,         
  CHARGE_STRENGTH: -50,      
  CENTER_STRENGTH: 0.05,    
  COLLIDE_RADIUS: 8,

  EXPANDED_LINK_DISTANCE: 80,
  EXPANDED_CHARGE_STRENGTH: -70,

  HOVER_ANIMATION_DURATION: 200,
  ZOOM_DURATION: 600,
  PULSE_DURATION: 3000,

  LINK_HIGHLIGHT_WIDTH: 3,
  NODE_HIGHLIGHT_SCALE: 1.3,
  LINK_DASH_SPEED: 0.5
}

// Highlight state for main graph
let highlightNodes = new Set()
let highlightLinks = new Set()
let draggedNode = null
let pulseTime = 0
let pulseAnimationId = null

// Colors for different node types
const TYPE_COLORS = {
  behavior: '#10b981',
  attribute: '#f59e0b', 
  function: '#ef4444',
  segment: '#06b6d4',
  trajectory: '#8b5cf6',
  default: '#6b7280'
}

// Highlight colors
const HIGHLIGHT_COLORS = {
  link: '#fbbf24',
  node: '#fbbf24',
  pulse: '#f59e0b'
}

// Node type definitions for legend
const nodeTypes = ref([
  { name: 'behavior', label: 'Behavior', color: '#10b981' },
  { name: 'attribute', label: 'Attribute', color: '#f59e0b' },
  { name: 'function', label: 'Function', color: '#ef4444' },
  { name: 'trajectory', label: 'Trajectory', color: '#8b5cf6' },
  { name: 'segment', label: 'Segment', color: '#06b6d4' },
])

// Computed properties
const availableLevels = computed(() => {
  if (!props.node.graph?.nodes) return [1]
  
  const levels = new Set()
  props.node.graph.nodes.forEach(node => {
    if (node.level > 0) {
      levels.add(node.level)
    }
  })
  
  const sortedLevels = Array.from(levels).sort()
  return sortedLevels.length > 0 ? sortedLevels : [1]
})

const hasGraphData = computed(() => {
  return props.node.graph?.nodes && props.node.graph.nodes.length > 1
})

const filteredNodes = computed(() => {
  if (!hasGraphData.value) return []
  
  const allNodes = props.node.graph.nodes
  return allNodes.filter(node => node.level <= props.currentLevel && node.level > 0)
})

const filteredLinks = computed(() => {
  if (!props.node.graph?.links) return []
  
  return props.node.graph.links.filter(link => link.level <= props.currentLevel)
})

const expandedFilteredNodes = computed(() => {
  if (!hasGraphData.value) return []
  
  const allNodes = props.node.graph.nodes
  return allNodes.filter(node => node.level <= expandedCurrentLevel.value && node.level > 0)
})

const expandedFilteredLinks = computed(() => {
  if (!props.node.graph?.links) return []
  
  return props.node.graph.links.filter(link => link.level <= expandedCurrentLevel.value)
})

// Build graph data for force-graph
const buildGraphData = (level = props.currentLevel) => {
  if (!hasGraphData.value) {
    return { nodes: [], links: [] }
  }

  // Create central node
  const centralNode = {
    id: props.nodeId,
    title: props.node.title,
    label: props.node.title,
    type: props.node.type || 'segment',
    level: 0,
    isCenter: true,
    neighbors: [],
    links: [],
    degree: 1
  }

  // Create related nodes
  const relatedNodes = (level === props.currentLevel ? filteredNodes.value : expandedFilteredNodes.value).map(node => ({
    id: node.id,
    title: node.title || node.label,
    label: node.label || node.title,
    type: node.type,
    level: node.level,
    isCenter: false,
    neighbors: [],
    links: [],
    degree: Math.floor(Math.random() * 3) + 1
  }))

  const allNodes = [centralNode, ...relatedNodes]
  const nodeById = new Map()
  allNodes.forEach(n => {
    nodeById.set(n.id, n)
  })

  // Create links
  const links = (level === props.currentLevel ? filteredLinks.value : expandedFilteredLinks.value)
    .map(link => ({ 
      source: link.source, 
      target: link.target,
      level: link.level 
    }))
    .filter(link => nodeById.has(link.source) && nodeById.has(link.target))

  // Build neighbor relationships
  links.forEach(link => {
    const sourceNode = nodeById.get(link.source)
    const targetNode = nodeById.get(link.target)
    
    if (sourceNode && targetNode) {
      sourceNode.neighbors.push(targetNode)
      targetNode.neighbors.push(sourceNode)
      sourceNode.links.push(link)
      targetNode.links.push(link)
      sourceNode.degree++
      targetNode.degree++
    }
  })

  return { nodes: allNodes, links }
}

// Debounce function for performance
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

function startPulseAnimation() {
  if (pulseAnimationId) {
    cancelAnimationFrame(pulseAnimationId)
  }
  
  const animate = () => {
    pulseTime = (pulseTime + 16) % ANIMATION_CONFIG.PULSE_DURATION
    
    pulseAnimationId = requestAnimationFrame(animate)
  }
  
  pulseAnimationId = requestAnimationFrame(animate)
}

function stopPulseAnimation() {
  if (pulseAnimationId) {
    cancelAnimationFrame(pulseAnimationId)
    pulseAnimationId = null
  }
}

function getPulseEffect() {
  const pulse = Math.sin(pulseTime * 0.002) * 0.5 + 0.5
  return {
    radius: 2 + pulse * 2,
    opacity: 0.3 + pulse * 0.3
  }
}

// Highlight connected nodes for main graph
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
  node.neighbors.forEach(n => newNodes.add(n))
  
  highlightNodes = newNodes
  highlightLinks = newLinks
  draggedNode = node
}

// Highlight connected nodes for expanded graph
function highlightExpandedConnectedNodes(node) {
  if (!node) {
    expandedHighlightNodes = new Set()
    expandedHighlightLinks = new Set()
    expandedDraggedNode = null
    return
  }

  const newNodes = new Set([node])
  const newLinks = new Set()
  
  node.links.forEach(l => newLinks.add(l))
  node.neighbors.forEach(n => newNodes.add(n))
  
  expandedHighlightNodes = newNodes
  expandedHighlightLinks = newLinks
  expandedDraggedNode = node
}

// Reset highlight for main graph
function clearHighlight() {
  highlightNodes = new Set()
  highlightLinks = new Set()
  draggedNode = null
}

// Reset highlight for expanded graph
function clearExpandedHighlight() {
  expandedHighlightNodes = new Set()
  expandedHighlightLinks = new Set()
  expandedDraggedNode = null
}

// Initialize force graph with dynamic effects
function initForceGraph() {
  if (!graphEl.value) return

  if (fg) {
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }

  const settings = {
    alphaMin: ANIMATION_CONFIG.ALPHA_MIN,
    alphaDecay: ANIMATION_CONFIG.ALPHA_DECAY, 
    velocityDecay: ANIMATION_CONFIG.VELOCITY_DECAY,
    linkDistance: ANIMATION_CONFIG.LINK_DISTANCE,
    chargeStrength: ANIMATION_CONFIG.CHARGE_STRENGTH, 
    centerStrength: ANIMATION_CONFIG.CENTER_STRENGTH, 
    collideRadius: ANIMATION_CONFIG.COLLIDE_RADIUS
  }

  try {
    const graphData = buildGraphData()
    
    fg = ForceGraph()(graphEl.value)
      .graphData(graphData)
      .backgroundColor('rgba(0,0,0,0)')
      .nodeId('id')
      .linkSource('source')
      .linkTarget('target')
      .d3AlphaMin(settings.alphaMin)
      .d3AlphaDecay(settings.alphaDecay)
      .d3VelocityDecay(settings.velocityDecay)
      .cooldownTicks(100)
      .warmupTicks(30)
      .enableNodeDrag(true)
      .nodeRelSize(PERFORMANCE_CONFIG.NODE_RADIUS)
      .linkWidth(link => {
        const level = link.level || 1
        return level === 1 ? 1.5 : 1
      })
      .nodeVal(node => {
        const baseSize = node.isCenter ? 8 : PERFORMANCE_CONFIG.NODE_RADIUS
        const degree = node.degree || 1
        return baseSize + Math.log2(degree) * 0.5
      })

    configureForces(fg, settings)

    fg.nodeCanvasObjectMode(() => 'replace')
      .nodeCanvasObject((node, ctx, globalScale) => {
        if (globalScale < 0.3) return
        
        const isHighlighted = highlightNodes.has(node)
        const isCenter = node.isCenter
        const nodeColor = isHighlighted ? HIGHLIGHT_COLORS.node : (TYPE_COLORS[node.type] || TYPE_COLORS.default)

        const baseRadius = isCenter ? 8 : PERFORMANCE_CONFIG.NODE_RADIUS
        const degree = node.degree || 1
        const radius = baseRadius + Math.log2(degree) * 0.5
        const highlightScale = isHighlighted ? ANIMATION_CONFIG.NODE_HIGHLIGHT_SCALE : 1
        const finalRadius = radius * highlightScale

        if (isHighlighted) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + 3, 0, 2 * Math.PI, false)
          ctx.fillStyle = `${HIGHLIGHT_COLORS.node}20`
          ctx.fill()
        }

        ctx.beginPath()
        ctx.arc(node.x, node.y, finalRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()

        if (isCenter) {
          const pulse = getPulseEffect()
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + pulse.radius, 0, 2 * Math.PI, false)
          ctx.strokeStyle = `${HIGHLIGHT_COLORS.pulse}${Math.floor(pulse.opacity * 255).toString(16).padStart(2, '0')}`
          ctx.lineWidth = 2
          ctx.stroke()
        }

        if (globalScale > 1.5) {
          const fontSize = Math.min(12, 10 / globalScale)
          ctx.font = `${fontSize}px system-ui`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'top'
          
          if (isCenter) {
            ctx.fillStyle = '#111827'
            ctx.fillText('Current node', node.x, node.y + finalRadius + 10 / globalScale)
          } else {
            ctx.fillStyle = '#374151'
            const label = node.label || node.id
            ctx.fillText(label, node.x, node.y + finalRadius + 2 / globalScale)
          }
        }
      })
      .linkCanvasObjectMode(() => 'after')
      .linkCanvasObject((link, ctx) => {
        if (!fg || fg.zoom() < 0.3) return
        
        const isHighlighted = highlightLinks.has(link)
        const level = link.level || 1

        const dashOffset = isHighlighted ? (pulseTime * ANIMATION_CONFIG.LINK_DASH_SPEED) % 10 : 0
        
        ctx.beginPath()
        ctx.moveTo(link.source.x, link.source.y)
        ctx.lineTo(link.target.x, link.target.y)
        
        if (isHighlighted) {
          ctx.strokeStyle = HIGHLIGHT_COLORS.link
          ctx.lineWidth = ANIMATION_CONFIG.LINK_HIGHLIGHT_WIDTH
          ctx.setLineDash([8, 4])
          ctx.lineDashOffset = -dashOffset
        } else {
          const opacity = Math.max(0.3, 1 - (level - 1) * 0.2)
          ctx.strokeStyle = `rgba(148,163,184,${opacity})`
          ctx.lineWidth = level === 1 ? 2 : 1
          
          if (level > 1) {
            ctx.setLineDash([4, 4])
            ctx.lineDashOffset = -dashOffset
          } else {
            ctx.setLineDash([])
          }
        }
        
        ctx.stroke()
      })
      .nodePointerAreaPaint((node, color, ctx) => {
        const baseRadius = node.isCenter ? 8 : PERFORMANCE_CONFIG.NODE_RADIUS
        const degree = node.degree || 1
        const radius = baseRadius + Math.log2(degree) * 0.5 + 2
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
      }, ANIMATION_CONFIG.HOVER_ANIMATION_DURATION))
      .onNodeDrag((node) => {
        highlightConnectedNodes(node)
      })
      .onNodeDragEnd(() => {
        fg.d3ReheatSimulation()
        clearHighlight()
      })
      .onNodeClick((node) => {
        if (node.id !== props.nodeId) {
          emit('open-node', node.id)
        }
      })

    fg.onZoom(() => {
      if (fg.zoom() < 0.5) {
        fg.linkWidth(0.5)
      } else {
        fg.linkWidth(link => link.level === 1 ? 1.5 : 1)
      }
    })

    // Set initial size
    updateGraphSize()
    
    // Auto-fit with animation
    setTimeout(() => {
      if (fg) {
        fg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 50)
        fg.d3ReheatSimulation()
      }
    }, 500)

    startPulseAnimation()
    
    console.log('✅ ForceGraph initialized with dynamic effects')
    
  } catch (error) {
    console.error('❌ Failed to initialize ForceGraph:', error)
  }
}

// Initialize expanded force graph with enhanced dynamic effects
function initExpandedForceGraph() {
  if (!expandedGraphEl.value) return

  if (expandedFg) {
    expandedFg.graphData({ nodes: [], links: [] })
    expandedFg = null
  }

  const settings = {
    alphaMin: ANIMATION_CONFIG.ALPHA_MIN,
    alphaDecay: ANIMATION_CONFIG.ALPHA_DECAY * 0.5,
    velocityDecay: ANIMATION_CONFIG.VELOCITY_DECAY,
    linkDistance: ANIMATION_CONFIG.EXPANDED_LINK_DISTANCE,
    chargeStrength: ANIMATION_CONFIG.EXPANDED_CHARGE_STRENGTH, 
    centerStrength: ANIMATION_CONFIG.CENTER_STRENGTH * 0.5,
    collideRadius: ANIMATION_CONFIG.COLLIDE_RADIUS * 1.5
  }

  try {
    const graphData = buildGraphData(expandedCurrentLevel.value)
    
    expandedFg = ForceGraph()(expandedGraphEl.value)
      .graphData(graphData)
      .backgroundColor('rgba(0,0,0,0)')
      .nodeId('id')
      .linkSource('source')
      .linkTarget('target')
      .d3AlphaMin(settings.alphaMin)
      .d3AlphaDecay(settings.alphaDecay)
      .d3VelocityDecay(settings.velocityDecay)
      .cooldownTicks(150)
      .warmupTicks(40)
      .enableNodeDrag(true)
      .nodeRelSize(PERFORMANCE_CONFIG.NODE_RADIUS + 1)
      .linkWidth(link => link.level === 1 ? 2 : 1.2)
      .nodeVal(node => {
        const baseSize = node.isCenter ? 12 : PERFORMANCE_CONFIG.NODE_RADIUS + 2
        const degree = node.degree || 1
        return baseSize + Math.log2(degree) * 1
      })

    configureForces(expandedFg, settings)

    expandedFg.nodeCanvasObjectMode(() => 'replace')
      .nodeCanvasObject((node, ctx, globalScale) => {
        if (globalScale < 0.3) return
        
        const isHighlighted = expandedHighlightNodes.has(node)
        const isCenter = node.isCenter
        const nodeColor = isHighlighted ? HIGHLIGHT_COLORS.node : (TYPE_COLORS[node.type] || TYPE_COLORS.default)

        const baseRadius = isCenter ? 12 : PERFORMANCE_CONFIG.NODE_RADIUS + 2
        const degree = node.degree || 1
        const radius = baseRadius + Math.log2(degree) * 1
        const highlightScale = isHighlighted ? ANIMATION_CONFIG.NODE_HIGHLIGHT_SCALE : 1
        const finalRadius = radius * highlightScale

        if (isHighlighted) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + 5, 0, 2 * Math.PI, false)
          ctx.fillStyle = `${HIGHLIGHT_COLORS.node}30`
          ctx.fill()
        }

        ctx.beginPath()
        ctx.arc(node.x, node.y, finalRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()

        if (isCenter) {
          const pulse = getPulseEffect()
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + pulse.radius * 1.5, 0, 2 * Math.PI, false)
          ctx.strokeStyle = `${HIGHLIGHT_COLORS.pulse}${Math.floor(pulse.opacity * 255).toString(16).padStart(2, '0')}`
          ctx.lineWidth = 3
          ctx.stroke()
        }

        if (globalScale > 0.8) {
          const fontSize = Math.min(16, 14 / globalScale)
          ctx.font = `${fontSize}px system-ui`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'top'
          
          if (isCenter) {
            ctx.fillStyle = '#111827'
            ctx.fillText('Current node', node.x, node.y + finalRadius + 15 / globalScale)
          } else {
            ctx.fillStyle = '#374151'
            const label = node.label || node.id
            ctx.fillText(label, node.x, node.y + finalRadius + 6 / globalScale)
          }
        }
      })
      .linkCanvasObjectMode(() => 'after')
      .linkCanvasObject((link, ctx) => {
        if (!expandedFg || expandedFg.zoom() < 0.3) return
        
        const isHighlighted = expandedHighlightLinks.has(link)
        const level = link.level || 1

        const dashOffset = (pulseTime * ANIMATION_CONFIG.LINK_DASH_SPEED) % 10
        
        ctx.beginPath()
        ctx.moveTo(link.source.x, link.source.y)
        ctx.lineTo(link.target.x, link.target.y)
        
        if (isHighlighted) {
          ctx.strokeStyle = HIGHLIGHT_COLORS.link
          ctx.lineWidth = ANIMATION_CONFIG.LINK_HIGHLIGHT_WIDTH + 1
          ctx.setLineDash([10, 5])
          ctx.lineDashOffset = -dashOffset
        } else {
          const opacity = Math.max(0.4, 1 - (level - 1) * 0.2)
          ctx.strokeStyle = `rgba(148,163,184,${opacity})`
          ctx.lineWidth = level === 1 ? 2.5 : 1.5
          
          if (level > 1) {
            ctx.setLineDash([6, 4])
            ctx.lineDashOffset = -dashOffset
          } else {
            ctx.setLineDash([])
          }
        }
        
        ctx.stroke()
      })
      .nodePointerAreaPaint((node, color, ctx) => {
        const baseRadius = node.isCenter ? 12 : PERFORMANCE_CONFIG.NODE_RADIUS + 2
        const degree = node.degree || 1
        const radius = baseRadius + Math.log2(degree) * 1 + 2
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
        ctx.fillStyle = color
        ctx.fill()
      })
      .onNodeHover(debounce((node) => {
        if (expandedDraggedNode) return
        
        if (!node) {
          expandedHighlightNodes = new Set()
          expandedHighlightLinks = new Set()
          return
        }

        const newNodes = new Set([node])
        const newLinks = new Set()
        
        node.neighbors.slice(0, 10).forEach(n => newNodes.add(n))
        node.links.slice(0, 15).forEach(l => newLinks.add(l))
        
        expandedHighlightNodes = newNodes
        expandedHighlightLinks = newLinks
      }, ANIMATION_CONFIG.HOVER_ANIMATION_DURATION))
      .onNodeDrag((node) => {
        highlightExpandedConnectedNodes(node)
      })
      .onNodeDragEnd(() => {
        expandedFg.d3ReheatSimulation()
        clearExpandedHighlight()
      })
      .onNodeClick((node) => {
        if (node.id !== props.nodeId) {
          emit('open-node', node.id)
        }
      })

    expandedFg.onZoom(() => {
      if (expandedFg.zoom() < 0.5) {
        expandedFg.linkWidth(0.8)
      } else {
        expandedFg.linkWidth(link => link.level === 1 ? 2 : 1.2)
      }
    })

    // Set initial size
    updateExpandedGraphSize()
    
    // Auto-fit with animation
    setTimeout(() => {
      if (expandedFg) {
        expandedFg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 80)
        expandedFg.d3ReheatSimulation()
      }
    }, 500)

    console.log('✅ Expanded ForceGraph initialized with enhanced dynamic effects')
    
  } catch (error) {
    console.error('❌ Failed to initialize expanded ForceGraph:', error)
  }
}

function configureForces(graphInstance, settings) {
  try {

    const linkForce = graphInstance.d3Force('link')
    if (linkForce && typeof linkForce.distance === 'function') {
      linkForce.distance(settings.linkDistance)
      linkForce.strength(0.1)  
    }

    const chargeForce = graphInstance.d3Force('charge')
    if (chargeForce && typeof chargeForce.strength === 'function') {
      chargeForce.strength(settings.chargeStrength)  
      if (typeof chargeForce.distanceMax === 'function') {
        chargeForce.distanceMax(settings.linkDistance * 2.5)
      }
    }

    const centerForce = graphInstance.d3Force('center')
    if (centerForce && typeof centerForce.strength === 'function') {
      centerForce.strength(settings.centerStrength)  
    }

    const collideForce = graphInstance.d3Force('collide')
    if (collideForce && typeof collideForce.radius === 'function') {
      collideForce.radius(settings.collideRadius)
      collideForce.strength(0.5)  
    }

  } catch (error) {
    console.warn('Force configuration warning:', error)
  }
}

function updateGraphSize() {
  if (!graphEl.value || !fg) return
  const rect = graphEl.value.getBoundingClientRect()
  fg.width(rect.width).height(rect.height)
}

function updateExpandedGraphSize() {
  if (!expandedGraphEl.value || !expandedFg) return
  const rect = expandedGraphEl.value.getBoundingClientRect()
  expandedFg.width(rect.width).height(rect.height)
}

const resizeHandler = debounce(() => {
  updateGraphSize()
  if (isGraphExpanded.value) {
    updateExpandedGraphSize()
  }
}, 200)

// Event handlers
const handleLevelClick = (level) => {
  console.log('Switching to level:', level)
  emit('switch-level', level)
}

const handleExpandedLevelClick = (level) => {
  expandedCurrentLevel.value = level
  refreshExpandedGraph()
}

const expandGraph = () => {
  isGraphExpanded.value = true
  nextTick(() => {
    if (expandedGraphEl.value) {
      initExpandedForceGraph()
    }
  })
}

const closeExpandedGraph = () => {
  isGraphExpanded.value = false
  if (expandedFg) {
    expandedFg.graphData({ nodes: [], links: [] })
    expandedFg = null
  }
  clearExpandedHighlight()
}

const refreshExpandedGraph = () => {
  if (expandedFg && hasGraphData.value) {
    const newGraphData = buildGraphData(expandedCurrentLevel.value)
    expandedFg.graphData(newGraphData)
    
    setTimeout(() => {
      if (expandedFg) {
        expandedFg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 80)
        expandedFg.d3ReheatSimulation()
      }
    }, 100)
  }
}

const emit = defineEmits(['open-node', 'switch-level'])

// Lifecycle
onMounted(async () => {
  await nextTick()
  
  if (graphEl.value && hasGraphData.value) {
    initForceGraph()
  }

  applyHighlight()
  
  window.addEventListener('resize', resizeHandler)
})

onUpdated(() => {
  applyHighlight()
})

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  stopPulseAnimation()
  
  if (fg) {
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }
  
  if (expandedFg) {
    expandedFg.graphData({ nodes: [], links: [] })
    expandedFg = null
  }
})

// Watchers
watch(() => props.currentLevel, () => {
  if (fg && hasGraphData.value) {
    const newGraphData = buildGraphData()
    fg.graphData(newGraphData)
    
    setTimeout(() => {
      if (fg) {
        fg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 50)
        fg.d3ReheatSimulation()
      }
    }, 100)
  }
})

watch(() => props.node, () => {
  if (fg && hasGraphData.value) {
    const newGraphData = buildGraphData()
    fg.graphData(newGraphData)
    
    setTimeout(() => {
      if (fg) {
        fg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 50)
        fg.d3ReheatSimulation()
      }
    }, 100)
  }

  applyHighlight()
})

watch(() => graphEl.value, (newEl) => {
  if (newEl && hasGraphData.value && !fg) {
    initForceGraph()
  }
})

watch(() => expandedCurrentLevel.value, () => {
  refreshExpandedGraph()
})

watch(() => isGraphExpanded.value, (newVal) => {
  if (newVal) {
    startPulseAnimation()
  }
})

watch(() => codeImplementation.value, (newCode) => {
  if (newCode) {
    detectedLanguage.value = detectLanguage(newCode)
    applyHighlight()
  }
}, { immediate: true })
</script>

<style scoped>
.page-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.main-content {
  flex: 1;
  min-width: 0; 
}

.graph-sidebar {
  width: 400px;
  min-width: 400px;
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  margin-right: -200px;
  margin-left: 20px;
}

.graph-main-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* Title block styles */
.title-block {
  margin-bottom: 14px;
}

.title {
  font-size: 30px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #0f172a;
}

/* Main content */
.body {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #111827;
}

.function-section {
  margin-bottom: 24px;
}

.function-description-content {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  margin: 12px 0;
  line-height: 1.6;
  font-size: 16px;
  color: #374151;
}

.code-section {
  margin-bottom: 24px;
}

.code-highlight-wrapper {
  margin-top: 8px;
  position: relative;
}

.code-language-label {
  position: absolute;
  top: 10px;
  right: 12px;
  font-size: 12px;
  color: #6b7280;
  background: rgba(255, 255, 255, 0.9);
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  font-family: system-ui, -apple-system, sans-serif;
  z-index: 2;
}

.code-block {
  margin: 0;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
  min-height: 60px;
}

.code-block code {
  display: block;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  color: #2d3748;
  white-space: pre;
  overflow-x: auto;
}

.description-list {
  padding-left: 18px;
  margin: 8px 0 16px;
}

.description-item {
  margin-bottom: 10px;
  color: #374151;
  line-height: 1.5;
  list-style-type: disc;
}

/* main description */
.main-description {
  margin-bottom: 4px;
  line-height: 1.5;
}

.main-description strong {
  font-weight: 600;
  color: #111827;
  display: block;
  margin-bottom: 8px;
}

.description-text {
  display: block;
  margin-top: 4px;
  line-height: 1.6;
}

.bullet-list {
  padding-left: 18px;
  margin: 4px 0 10px;
  font-size: 13px;
  color: #374151;
}

.bullet-list li {
  margin-bottom: 4px;
}

.detailed-section {
  margin: 24px 0 20px;
  padding-top: 20px;
  border-top: 2px solid #e5e7eb;
}

.detailed-section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #111827;
}

.detailed-descriptions-container {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin: 12px 0;
  border: 1px solid #e5e7eb;
}

.detailed-description-item {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.detailed-description-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.detailed-item-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-index {
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  min-width: 24px;
}

.detailed-item-title {
  font-size: 15px;
  color: #111827;
  font-weight: 600;
}

.detailed-item-content {
  display: flex;
  padding: 12px 16px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.detailed-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #4b5563;
}

/* Attribute header styles */
.attribute-header {
  background: #f8fafc;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #e5e7eb;
  border-left: 4px solid #1e40af; 
}

.attribute-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.attribute-summary-item {
  background: white;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.attribute-summary-item strong {
  display: block;
  margin-bottom: 8px;
  color: #111827;
  font-size: 15px;
}

.attribute-summary-item p {
  margin: 0;
  color: #4b5563;
  line-height: 1.5;
}

.statistics-content {
  margin-top: 8px;
}

.behavior-associations {
  margin-top: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.top-behavior,
.association-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.top-behavior:last-child,
.association-count:last-child {
  margin-bottom: 0;
}

.top-behavior .label,
.association-count .label {
  font-weight: 500;
  color: #374151;
  font-size: 13px;
  min-width: 120px;
}

.top-behavior .value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #111827;
  font-weight: 600;
}

.top-behavior .description {
  color: #6b7280;
  font-size: 13px;
  font-style: italic;
}

.association-count .value {
  font-weight: 600;
  color: #3b82f6;
  font-size: 14px;
}

/* Graph section styles */
.graph-section {
  margin: 0;
  padding: 20px;
  border-top: none;
}

.graph-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.graph-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.expand-btn {
  padding: 6px 10px;
  background: #f8fafc;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
  color: #111827;
}

.graph-header {
  margin-bottom: 16px;
}

.graph-controls {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.control-label {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  padding-top: 4px;
}

.level-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.level-btn {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.level-btn:hover {
  background: #f8fafc;
  border-color: #9ca3af;
  color: #111827;
}

.level-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.level-badge {
  font-size: 11px;
  padding: 1px 4px;
  background: #ef4444;
  color: white;
  border-radius: 4px;
}

.graph-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

/* Graph wrapper styles */
.graph-wrapper {
  position: relative;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  overflow: hidden;
  height: 350px;
}

.graph-canvas {
  width: 100%;
  height: 100%;
}

/* Legend */
.graph-legend {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.legend-title {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.legend-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.1)
}

.legend-label {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}

.graph-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.graph-modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 1200px;
  height: 90%;
  max-height: 900px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.graph-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
}

.graph-modal-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.close-btn {
  padding: 8px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
  color: #111827;
}

.graph-modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  overflow: hidden;
}

.graph-modal-controls {
  margin-bottom: 20px;
}

.graph-modal-canvas-wrapper {
  flex: 1;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  overflow: hidden;
  margin-bottom: 20px;
}

.graph-modal-canvas {
  width: 100%;
  height: 100%;
}

.graph-modal-legend {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.graph-wrapper {
  position: relative;
  transition: all 0.3s ease;
}

.graph-wrapper:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

@media (max-width: 1200px) {
  .page-container {
    flex-direction: column;
  }
  
  .graph-sidebar {
    width: 100%;
    min-width: 100%;
    position: static;
    margin: 20px 0 0 0;
  }
  
  .graph-main-container {
    margin-top: 0;
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 18px;
  }
  
  .graph-wrapper {
    height: 300px;
  }
  
  .legend-items {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .graph-modal-content {
    width: 95%;
    height: 95%;
  }
  
  .graph-modal-header {
    padding: 16px;
  }
  
  .graph-modal-body {
    padding: 16px;
  }
  
  .detailed-descriptions-container {
    padding: 16px;
  }
  
  .detailed-item-content {
    padding: 10px 14px;
  }
  
  .function-description-content {
    padding: 16px;
    font-size: 14px;
  }
  
  .code-block {
    padding: 16px;
    font-size: 13px;
  }
  
  .code-language-label {
    font-size: 11px;
    padding: 2px 8px;
  }
}

@media (max-width: 480px) {
  .graph-container {
    padding: 16px;
  }
  
  .graph-wrapper {
    height: 250px;
  }
  
  .graph-controls {
    gap: 8px;
  }
  
  .control-group {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .legend-items {
    grid-template-columns: 1fr;
  }
  
  .graph-modal-title {
    font-size: 16px;
  }
  
  .detailed-section {
    margin: 20px 0 16px;
    padding-top: 16px;
  }
  
  .detailed-descriptions-container {
    padding: 12px;
  }
  
  .detailed-description-item {
    margin-bottom: 16px;
    padding-bottom: 16px;
  }
  
  .detailed-item-content {
    padding: 8px 12px;
  }
  
  .detailed-text {
    font-size: 13px;
  }
  
  .function-description-content {
    padding: 12px;
    font-size: 14px;
  }
  
  .code-block {
    padding: 12px;
    font-size: 12px;
  }
  
  .code-language-label {
    font-size: 10px;
    padding: 1px 6px;
  }
}

/* Increase the font size of the entire page */
.title {
  font-size: 30px;
}

.section-title {
  font-size: 34px; /* Enlarge the subtitle to 22px */
}

.description-list li,
.bullet-list li {
  font-size: 34px; /* Enlarge the main text to 16px */
  line-height: 1.7;
}

.function-description-content {
  font-size: 28px;
  line-height: 1.6;
}

.code-block {
  font-size: 24px;
  line-height: 1.6;
  padding: 24px;
}

.code-language-label {
  font-size: 20px;
  padding: 6px 14px;
}

.detailed-section-title {
  font-size: 34px;
}

.detailed-item-title {
  font-size: 30px;
}

.detailed-text {
  font-size: 30px;
  line-height: 1.7;
}

.detail-index {
  font-size: 28px;
}

@media (min-width: 769px) {
  .attribute-summary-item strong {
    font-size: 30px;
  }
  
  .attribute-summary-item p {
    font-size: 28px;
    line-height: 1.6;
  }
  
  .top-behavior .label,
  .association-count .label {
    font-size: 26px;
    min-width: 200px;
  }
  
  .top-behavior .value {
    font-size: 24px;
    padding: 4px 10px;
  }
  
  .top-behavior .description {
    font-size: 24px;
  }
  
  .association-count .value {
    font-size: 26px;
  }
}

:deep(.hljs) {
  background: transparent !important;
}

:deep(.hljs-keyword) {
  color: #d73a49 !important;
  font-weight: 500 !important;
}

:deep(.hljs-string) {
  color: #032f62 !important;
}

:deep(.hljs-comment) {
  color: #6a737d !important;
  font-style: italic !important;
}

:deep(.hljs-number) {
  color: #005cc5 !important;
}

:deep(.hljs-title) {
  color: #6f42c1 !important;
}

:deep(.hljs-function) {
  color: #6f42c1 !important;
}

:deep(.hljs-params) {
  color: #24292e !important;
}

:deep(.hljs-built_in) {
  color: #e36209 !important;
}

:deep(.hljs-attr) {
  color: #005cc5 !important;
}

:deep(.hljs-name) {
  color: #e36209 !important;
}

.function-description-plain {
  margin: 12px 0;
  line-height: 1.6;
  font-size: 28px;
  color: #374151;
  padding: 0;
  background: none;
  border: none;
}

.code-plain {
  margin: 12px 0 0 0;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  font-size: 24px;
  line-height: 1.6;
  min-height: 60px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #2d3748;
}
</style>