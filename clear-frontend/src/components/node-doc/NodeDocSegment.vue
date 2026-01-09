<template>
  <!-- Title & meta area -->
  <header class="title-block">
    <h1 class="title">
      {{ node.title }}
    </h1>
    <!-- Meta information -->
    <div class="meta-info">
      
      <!-- Current level information -->
      <div class="meta-item" v-if="availableLevels.length > 1">
        <span class="label">Current Level:</span>
        <span class="value">Level {{ currentLevel }}</span>
      </div>
    </div>
  </header>

  <!-- Main content-->
  <section class="body">
    <div class="graph-floating" v-if="hasGraphData">
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
          
          <!-- Combine Show levels and Node Types -->
          <div class="graph-controls" style="display: flex; align-items: center; gap: 24px; flex-wrap: wrap;">
            <!-- Show levels -->
            <div class="control-group">
              <span class="control-label">Show levels:</span>
              <div class="level-buttons">
                <button
                  v-for="level in availableLevels"
                  :key="level"
                  class="level-btn"
                  :class="{
                    active: currentLevel === level
                  }"
                  @click="handleLevelClick(level)"
                >
                  Level {{ level }}
                  <span v-if="level > currentLevel" class="level-badge">View</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="graph-container">
          <div class="graph-wrapper">
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
            <div class="control-group">

            </div>
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

    <!-- Static Attributes -->
    <template v-if="filteredStaticAttributes.length">
      <h2 class="section-title">Static Attributes</h2>
      <ul class="bullet-list">
        <li v-for="(item, idx) in filteredStaticAttributes" :key="'attr-' + idx">
          <!-- 使用 v-html 渲染加粗部分 -->
          <span v-html="formatStaticAttribute(item)"></span>
        </li>
      </ul>
      <div style="height: 1px; background: #e5e7eb; margin: 20px 0;"></div>
    </template>

    <!-- Behavior Pattern -->
    <template v-if="hasBehaviorData">
      <h2 class="section-title">Behavior Pattern</h2>
      
      <ul class="bullet-list">
        <template v-if="hasContextData">
          <li><strong>Context:</strong></li>
          <ul class="bullet-list" style="margin-left: 20px;">
            <!-- Current Behavior -->
            <template v-if="node.context?.current_behavior">
              <li>
                <strong>Current Behavior:</strong> {{ currentBehaviorIntent }}
              </li>
            </template>

            <!-- Previous Behavior -->
            <template v-if="node.context?.previous_behavior && Object.keys(node.context.previous_behavior).length > 0">
              <li>
                <strong>Previous Behavior:</strong> {{ previousBehaviorIntent }}
              </li>
            </template>

            <!-- Next Behavior -->
            <template v-if="node.context?.next_behavior && Object.keys(node.context.next_behavior).length > 0">
              <li>
                <strong>Next Behavior:</strong> {{ nextBehaviorIntent }}
              </li>
            </template>
          </ul>
        </template>

        <!-- Explanation Section -->
        <template v-if="hasExplanationData">
          <li><strong>Explanation:</strong></li>
          <ul class="bullet-list" style="margin-left: 20px;">
            <!-- SD-KG Support - Display based on behavior_estimator.graph_support -->
            <template v-if="hasSdkgSupport">
              <li>
                <strong style="color: #dc2626;">SD-KG Support:</strong> 
                <span style="color: #dc2626;">{{ sdkgSupportText }}</span>
              </li>
            </template>

            <!-- Contextual Justification - Always displayed, default content shown if no data -->
            <li>
              <strong>Contextual Justification:</strong> {{ contextualJustificationText }}
            </li>
          </ul>
        </template>
      </ul>

      <!-- Add divider -->
      <div style="height: 1px; background: #e5e7eb; margin: 20px 0;"></div>
    </template>

    <!-- Underlying Cause -->
    <template v-if="hasUnderlyingCauseData">
      <h2 class="section-title">Underlying Cause</h2>
      <ul class="bullet-list">
        <!-- Regulatory Rule Cue -->
        <li>
          <strong>Regulatory Rule Cue:</strong> {{ regulatoryRuleCueText }}
        </li>

        <!-- Operational protocols -->
        <li>
          <strong>Operational Protocols:</strong> {{ operationalProtocolsText }}
        </li>
      </ul>
      <!-- Add divider -->
      <div style="height: 1px; background: #e5e7eb; margin: 20px 0;"></div>
    </template>

    <!-- Imputation Function -->
    <template v-if="hasImputationFunctionData">
      <h2 class="section-title">Imputation Function</h2>
      <ul class="bullet-list">
        <!-- Function Name -->
        <li>
          <strong>Function Name:</strong> {{ functionNameText }}
        </li>

        <!-- SD-KG Support - Display based on method_selector.statistical_support -->
        <template v-if="hasImputationSdkgSupport">
          <li>
            <strong style="color: #dc2626;">SD-KG Support:</strong> 
            <span style="color: #dc2626;">{{ imputationSdkgSupportText }}</span>
          </li>
        </template>
      </ul>
    </template>

    <template v-if="node.pattern && node.pattern.length">
      <h2 class="section-title">Relation to behaviors</h2>
      <ul class="bullet-list">
        <li v-for="(item, idx) in node.pattern" :key="'pat-' + idx">
          {{ item }}
        </li>
      </ul>
      <!-- Add divider -->
      
    </template>

    <template v-if="node.notes && node.notes.length">
      <h2 class="section-title">Notes for analysts</h2>
      <ul class="bullet-list">
        <li v-for="(item, idx) in node.notes" :key="'note-' + idx">
          {{ item }}
        </li>
      </ul>
    </template>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import ForceGraphModule from 'force-graph'

const ForceGraph = ForceGraphModule.default || ForceGraphModule

const isGraphExpanded = ref(false)
const expandedGraphEl = ref(null)
let expandedFg = null
const expandedCurrentLevel = ref(2) 

let expandedHighlightNodes = new Set()
let expandedHighlightLinks = new Set()
let expandedDraggedNode = null

// Imputation Function related
const hasImputationFunctionData = computed(() => {
  return true // Function Name is always displayed, so this section is always shown
})

const functionNameText = computed(() => {
  return "Linear interpolation" // Keep default content
})

const hasImputationSdkgSupport = computed(() => {
  return props.node?.method_selector?.statistical_support && 
         props.node.method_selector.statistical_support.trim().length > 0
})

const imputationSdkgSupportText = computed(() => {
  // Use real data if method_selector.statistical_support exists
  if (props.node?.method_selector?.statistical_support) {
    return props.node.method_selector.statistical_support
  }
  // Otherwise, use default content (even though it won't display, keep as fallback)
  return "Selected based on SD-KG pattern matching for vessels exhibiting stable navigation behavior in approach phases."
})

// Computed properties
const hasSdkgSupport = computed(() => {
  return props.node?.behavior_estimator?.graph_support && 
         props.node.behavior_estimator.graph_support.trim().length > 0
})
const formatStaticAttribute = (item) => {
  const colonIndex = item.indexOf(':')
  if (colonIndex !== -1) {
    const label = item.substring(0, colonIndex)
    const value = item.substring(colonIndex + 1)
    return `<strong>${label}:</strong>${value}`
  }
  return item
}
// Underlying Cause related
const hasUnderlyingCauseData = computed(() => {
  return true // Always display the Underlying Cause section
})

const regulatoryRuleCueText = computed(() => {
  // Use real data if explanation_composer.regulatory_rule_cue exists
  if (props.node?.explanation_composer?.regulatory_rule_cue) {
    return props.node.explanation_composer.regulatory_rule_cue
  }
  // Otherwise, use default content
  return "Vessels must reduce speed before entering controlled harbor zones and adjust heading to merge into inbound traffic lanes."
})

const operationalProtocolsText = computed(() => {
  // Use real data if explanation_composer.operational_protocol_rationale exists
  if (props.node?.explanation_composer?.operational_protocol_rationale) {
    return props.node.explanation_composer.operational_protocol_rationale
  }
  // Otherwise, use default content
  return "Large tankers often perform a smooth decelerate–align maneuver prior to pilot boarding to stabilize motion and ensure predictable handling."
})

const sdkgSupportText = computed(() => {
  // Use real data if behavior_estimator.graph_support exists
  if (props.node?.behavior_estimator?.graph_support) {
    return props.node.behavior_estimator.graph_support
  }
  // Otherwise, use default content
  return "Conditioned on Navigation status = Underway using engine and Vessel type = Tanker, the SD-KG estimates P(Port-Entry: Decelerate–Align) ≈ 0.58, which ranks 1st learned behavior patterns for this context."
})

const contextualJustificationText = computed(() => {
  // Use real data if behavior_estimator.contextual_justification exists
  if (props.node?.behavior_estimator?.contextual_justification) {
    return props.node.behavior_estimator.contextual_justification
  }
  // Otherwise, use default content
  return "The segment occurs at the harbor entrance where inbound vessels are expected to slow down and align to the designated lane."
})

const hasExplanationData = computed(() => {
  // Display Explanation if either SD-KG Support or Contextual Justification has data
  return hasSdkgSupport.value || true // Contextual Justification is always displayed, so this always returns true
})

const props = defineProps({
  nodeId: {
    type: String,
    required: true
  },
  node: {
    type: Object,
    required: true
  }
})

const filteredStaticAttributes = computed(() => {
  if (!props.node?.static_attributes) return []
  
  // 修改这里：移除筛选条件，直接返回所有静态属性
  return props.node.static_attributes
})

const formatKey = (key) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const currentBehaviorIntent = computed(() => {
  return props.node?.context?.current_behavior?.intent || "No intent data available"
})

const previousBehaviorIntent = computed(() => {
  return props.node?.context?.previous_behavior?.intent || "No intent data available"
})

const nextBehaviorIntent = computed(() => {
  return props.node?.context?.next_behavior?.intent || "No intent data available"
})

// Computed properties
const hasBehaviorData = computed(() => {
  return hasContextData.value || hasExplanationData.value
})

const hasContextData = computed(() => {
  return props.node?.context && (
    (props.node.context.current_behavior && Object.keys(props.node.context.current_behavior).length > 0) ||
    (props.node.context.previous_behavior && Object.keys(props.node.context.previous_behavior).length > 0) ||
    (props.node.context.next_behavior && Object.keys(props.node.context.next_behavior).length > 0)
  )
})

// Graph references and state
const graphEl = ref(null)
let fg = null
const currentLevel = ref(2) // Default to displaying level 2

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
  return allNodes.filter(node => node.level <= currentLevel.value && node.level > 0)
})

const filteredLinks = computed(() => {
  if (!props.node.graph?.links) return []
  
  return props.node.graph.links.filter(link => link.level <= currentLevel.value)
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
const buildGraphData = (isExpanded = false) => {
  if (!hasGraphData.value) {
    return { nodes: [], links: [] }
  }

  // Create central node
  const centralNode = {
    id: props.nodeId,
    title: props.node.title,
    label: props.node.title,
    type: 'segment',
    level: 0,
    isCenter: true,
    neighbors: [],
    links: [],
    degree: 1,
    trajectory_id: props.node.trajectory_id,
    vessel_id: props.node.vessel_id
  }

  // Create related nodes 
  const relatedNodes = (isExpanded ? expandedFilteredNodes.value : filteredNodes.value).map(node => ({
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
  const links = (isExpanded ? expandedFilteredLinks.value : filteredLinks.value)
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

// Debounce function
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
    const graphData = buildGraphData(false)
    
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
        const baseSize = node.isCenter ? 10 : PERFORMANCE_CONFIG.NODE_RADIUS
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

        const baseRadius = isCenter ? 10 : PERFORMANCE_CONFIG.NODE_RADIUS
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

        if (globalScale > 1.5) {
          const fontSize = Math.min(12, 10 / globalScale)
          ctx.font = `${fontSize}px system-ui`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'top'

          if (node.isCenter) {
            ctx.fillStyle = '#111827' 
            ctx.fillText('Current node', node.x, node.y + finalRadius + 12 / globalScale)
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
        const baseRadius = node.isCenter ? 10 : PERFORMANCE_CONFIG.NODE_RADIUS
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
    
    console.log('✅ ForceGraph initialized for segment detail view')
    
  } catch (error) {
    console.error('❌ Failed to initialize ForceGraph:', error)
  }
}

// Initialize expanded force graph
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
    const graphData = buildGraphData(true)
    
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
      .nodeRelSize(PERFORMANCE_CONFIG.NODE_RADIUS + 2)
      .linkWidth(link => link.level === 1 ? 2 : 1.5)
      .nodeVal(node => {
        const baseSize = node.isCenter ? 15 : PERFORMANCE_CONFIG.NODE_RADIUS + 3
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

        const baseRadius = isCenter ? 15 : PERFORMANCE_CONFIG.NODE_RADIUS + 3
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

          if (node.isCenter) {
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
        const baseRadius = node.isCenter ? 15 : PERFORMANCE_CONFIG.NODE_RADIUS + 3
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
        expandedFg.linkWidth(1)
      } else {
        expandedFg.linkWidth(link => link.level === 1 ? 2 : 1.5)
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
      linkForce.strength(0.15)
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
  currentLevel.value = level
  refreshGraph()
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

const refreshGraph = () => {
  if (fg && hasGraphData.value) {
    const newGraphData = buildGraphData(false)
    fg.graphData(newGraphData)
    
    setTimeout(() => {
      if (fg) {
        fg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 50)
        fg.d3ReheatSimulation()
      }
    }, 100)
  }
}

const refreshExpandedGraph = () => {
  if (expandedFg && hasGraphData.value) {
    const newGraphData = buildGraphData(true)
    expandedFg.graphData(newGraphData)
    
    setTimeout(() => {
      if (expandedFg) {
        expandedFg.zoomToFit(ANIMATION_CONFIG.ZOOM_DURATION, 80)
        expandedFg.d3ReheatSimulation()
      }
    }, 100)
  }
}

const getLevelDescription = (level) => {
  const descriptions = {
    1: 'Direct connections',
    2: '2nd degree connections'
  }
  return descriptions[level] || `Level ${level}`
}

const emit = defineEmits(['open-node'])

// Lifecycle
onMounted(async () => {
  await nextTick()
  
  if (graphEl.value && hasGraphData.value) {
    initForceGraph()
  }
  
  window.addEventListener('resize', resizeHandler)
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
watch(() => props.node, () => {
  if (hasGraphData.value) {
    refreshGraph()
  }
})

watch(() => graphEl.value, (newEl) => {
  if (newEl && hasGraphData.value && !fg) {
    initForceGraph()
  }
})

watch(() => currentLevel.value, () => {
  refreshGraph()
})

watch(() => expandedCurrentLevel.value, () => {
  refreshExpandedGraph()
})

watch(() => isGraphExpanded.value, (newVal) => {
  if (newVal) {
    startPulseAnimation()
  }
})
</script>

<style scoped>
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

.summary {
  font-size: 13px;
  color: #4b5563;
  margin: 0 0 10px 0;
}

.meta-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #f8fafc;
  border-radius: 6px;
}

.label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.value {
  font-size: 13px;
  color: #111827;
  font-weight: 600;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
}

/* Main content */
.body {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  position: relative;
  padding-right: 260px; 
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #111827;
}

.body-paragraph {
  font-size: 13px;
  line-height: 1.6;
  color: #374151;
  margin: 0 0 8px 0;
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

.graph-floating {
  position: absolute;
  right: -200px;
  top: 20px;
  width: 400px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  z-index: 10;
}

/* Graph section styles */
.graph-section {
  margin: 0;
  padding: 0;
  border-top: none;
}

.graph-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
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

.layout-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
}

.reset-btn {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background: #f8fafc;
  border-color: #9ca3af;
}

.level-info {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  background: #f8fafc;
  padding: 6px 12px;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.graph-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #10b981;
  line-height: 1.5;
}

.graph-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.subsection-title {
  font-size: 12px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: #111827;
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
  border: 1px solid rgba(0, 0, 0, 0.1);
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
  font-size: 50px;
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

/* Responsive design */
@media (max-width: 1200px) {
  .graph-floating {
    position: static;
    width: 100%;
    margin-top: 20px;
  }
  
  .body {
    padding-right: 0;
  }
}

@media (max-width: 1024px) {
  .graph-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .graph-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 18px;
  }
  
  .meta-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .meta-item {
    width: 100%;
    justify-content: space-between;
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
}

.subsubsection-title {
  font-size: 11px;
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: #374151;
  padding-left: 12px;
  border-left: 2px solid #6b7280;
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
}

/* 放大Static Attributes和Behavior Pattern的标题 */
.section-title {
  font-size: 30px !important;
  font-weight: 700 !important;
}

/* 放大这两个部分的正文 */
.bullet-list li,
.bullet-list .bullet-list li {
  font-size: 30px !important;
}
</style>