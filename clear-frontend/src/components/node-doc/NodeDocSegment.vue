<template>
  <!-- Two-column layout container -->
  <div class="page-container">
    <!-- Left column: Main content area -->
    <div class="main-content">
      <!-- Title & meta information section -->
      <header class="title-block">
        <h1 class="title">
          {{ node.title }}
        </h1>
        <!-- Meta information display -->
        <div class="meta-info">
          <!-- Current level indicator (if multiple levels available) -->
          <div class="meta-item" v-if="availableLevels.length > 1">
            <span class="label">Current Level:</span>
            <span class="value">Level {{ currentLevel }}</span>
          </div>
        </div>
      </header>

      <!-- Main content area -->
      <section class="body">
        <!-- Static Attributes section -->
        <template v-if="filteredStaticAttributes.length">
          <h2 class="section-title">Static Attributes</h2>
          <ul class="bullet-list">
            <li v-for="(item, idx) in filteredStaticAttributes" :key="'attr-' + idx">
              <span v-html="formatStaticAttributeForDisplay(item)"></span>
              <!-- Additional details for Spatial Context attributes -->
              <template v-if="getStaticAttributeLabel(item) === 'Spatial context' && getStaticAttributeDetails(item)">
                <div class="attribute-details">
                  {{ getStaticAttributeDetails(item) }}
                </div>
              </template>
            </li>
          </ul>
          <div class="section-divider"></div>
        </template>

        <!-- Behavior Pattern section -->
        <template v-if="hasBehaviorData">
          <h2 class="section-title">Behavior Pattern</h2>
          
          <ul class="bullet-list">
            <!-- Context data (if available) -->
            <template v-if="hasContextData">
              <li><strong>Context:</strong></li>
              <ul class="bullet-list nested-list">
                <!-- Current Behavior -->
                <template v-if="node.context?.current_behavior">
                  <li>
                    <strong>Current Behavior:</strong> 
                    <span 
                      class="clickable-behavior" 
                      @click="highlightCurrentBehavior"
                      :title="currentBehaviorTitle"
                    >
                      {{ currentBehaviorTitle }}
                    </span>
                  </li>
                </template>

                <!-- Previous Behavior -->
                <template v-if="node.context?.previous_behavior && Object.keys(node.context.previous_behavior).length > 0">
                  <li>
                    <strong>Previous Behavior:</strong> {{ previousBehaviorTitle }}
                  </li>
                </template>

                <!-- Next Behavior -->
                <template v-if="node.context?.next_behavior && Object.keys(node.context.next_behavior).length > 0">
                  <li>
                    <strong>Next Behavior:</strong> {{ nextBehaviorTitle }}
                  </li>
                </template>
              </ul>
            </template>

            <!-- Detailed Description Section -->
            <template v-if="hasBehaviorDetails">
              <li><strong>Detailed Description:</strong></li>
              <ul class="bullet-list nested-list">
                <!-- Current Behavior Details -->
                <template v-if="currentBehaviorDescription">
                  <li>
                    <strong>Current Behavior:</strong> {{ currentBehaviorDescription }}
                  </li>
                </template>

                <!-- Previous Behavior Details -->
                <template v-if="previousBehaviorDescription">
                  <li>
                    <strong>Previous Behavior:</strong> {{ previousBehaviorDescription }}
                  </li>
                </template>

                <!-- Next Behavior Details -->
                <template v-if="nextBehaviorDescription">
                  <li>
                    <strong>Next Behavior:</strong> {{ nextBehaviorDescription }}
                  </li>
                </template>
              </ul>
            </template>

            <!-- Explanation Section -->
            <template v-if="hasExplanationData">
              <li><strong>Explanation:</strong></li>
              <ul class="bullet-list nested-list">
                <!-- SD-KG Support - Display based on behavior_estimator.graph_support -->
                <template v-if="hasSdkgSupport">
                  <li>
                    <strong class="sdkg-highlight">SD-KG Support:</strong> 
                    <span class="sdkg-highlight">{{ sdkgSupportText }}</span>
                  </li>
                </template>

                <!-- Contextual Justification - Always displayed -->
                <li>
                  <strong>Contextual Justification:</strong> {{ contextualJustificationText }}
                </li>
              </ul>
            </template>
          </ul>

          <div class="section-divider"></div>
        </template>

        <!-- Underlying Cause section -->
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
          <div class="section-divider"></div>
        </template>

        <!-- Imputation Function section -->
        <template v-if="hasImputationFunctionData">
          <h2 class="section-title">Imputation Function</h2>
          <ul class="bullet-list">
            <!-- Function Name -->
            <li>
              <strong>Function Name:</strong> 
              <span 
                class="clickable-function" 
                @click="highlightImputationFunction"
                :title="functionNameText"
              >
                {{ functionNameText }}
              </span>
            </li>

            <!-- SD-KG Support for imputation -->
            <template v-if="hasImputationSdkgSupport">
              <li>
                <strong class="sdkg-highlight">SD-KG Support:</strong> 
                <span class="sdkg-highlight">{{ imputationSdkgSupportText }}</span>
              </li>
            </template>
          </ul>
        </template>

        <!-- Relation to behaviors section -->
        <template v-if="node.pattern && node.pattern.length">
          <h2 class="section-title">Relation to behaviors</h2>
          <ul class="bullet-list">
            <li v-for="(item, idx) in node.pattern" :key="'pat-' + idx">
              {{ item }}
            </li>
          </ul>
          <div class="section-divider"></div>
        </template>

        <!-- Notes for analysts section -->
        <template v-if="node.notes && node.notes.length">
          <h2 class="section-title">Notes for analysts</h2>
          <ul class="bullet-list">
            <li v-for="(item, idx) in node.notes" :key="'note-' + idx">
              {{ item }}
            </li>
          </ul>
        </template>
      </section>
    </div>

    <!-- Right column: Knowledge graph sidebar -->
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
          </div>
          
          <div class="graph-container">
            <div class="graph-wrapper">
              <div ref="graphEl" class="graph-canvas"></div>
            </div>
          </div>

          <!-- Graph legend -->
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

    <!-- Expanded graph modal (fullscreen view) -->
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
// Import Vue composition API and force-graph library
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import ForceGraphModule from 'force-graph'

const ForceGraph = ForceGraphModule.default || ForceGraphModule

// Graph expansion state
const isGraphExpanded = ref(false)
const expandedGraphEl = ref(null)
let expandedFg = null
const expandedCurrentLevel = ref(2) // Default expanded view level

// Highlight state for expanded graph
let expandedHighlightNodes = new Set()
let expandedHighlightLinks = new Set()
let expandedDraggedNode = null

// Track current highlighted node
const currentHighlightedNodeId = ref(null)

// Component props definition
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

// Computed property: Check if imputation function data is available
const hasImputationFunctionData = computed(() => {
  return true // Function Name is always displayed
})

// Computed property: Get imputation function name
const functionNameText = computed(() => {
  return "Linear interpolation" // Default function name
})

// Computed property: Check if SD-KG support exists for imputation
const hasImputationSdkgSupport = computed(() => {
  return props.node?.method_selector?.statistical_support && 
         props.node.method_selector.statistical_support.trim().length > 0
})

// Computed property: Get SD-KG support text for imputation
const imputationSdkgSupportText = computed(() => {
  // Use real data if available
  if (props.node?.method_selector?.statistical_support) {
    return props.node.method_selector.statistical_support
  }
  // Default fallback text
  return "Selected based on SD-KG pattern matching for vessels exhibiting stable navigation behavior in approach phases."
})

// Computed property: Check if SD-KG support exists for behavior
const hasSdkgSupport = computed(() => {
  return props.node?.behavior_estimator?.graph_support && 
         props.node.behavior_estimator.graph_support.trim().length > 0
})

// Format static attribute for display with clickable values
const formatStaticAttributeForDisplay = (item) => {
  const colonIndex = item.indexOf(':')
  if (colonIndex !== -1) {
    const label = item.substring(0, colonIndex)
    const value = item.substring(colonIndex + 1)

    if (label.toLowerCase().includes('spatial context')) {
      const firstCommaIndex = value.indexOf(',')
      if (firstCommaIndex !== -1) {
        const firstPart = value.substring(0, firstCommaIndex)
        return `<strong>${label}:</strong> <span class="clickable-attr" data-attr="${label.trim()}" data-value="${firstPart.trim()}">${firstPart}</span>`
      }
    }
    return `<strong>${label}:</strong> <span class="clickable-attr" data-attr="${label.trim()}" data-value="${value.trim()}">${value}</span>`
  }
  return `<span class="clickable-attr" data-attr="${item}" data-value="${item}">${item}</span>`
}

// Get label from static attribute string
const getStaticAttributeLabel = (item) => {
  const colonIndex = item.indexOf(':')
  if (colonIndex !== -1) {
    return item.substring(0, colonIndex).trim()
  }
  return item
}

// Get additional details from static attribute (for Spatial Context)
const getStaticAttributeDetails = (item) => {
  const colonIndex = item.indexOf(':')
  if (colonIndex !== -1) {
    const label = item.substring(0, colonIndex)
    const value = item.substring(colonIndex + 1)

    if (label.toLowerCase().includes('spatial context')) {
      const firstCommaIndex = value.indexOf(',')
      if (firstCommaIndex !== -1) {
        return value.substring(firstCommaIndex + 1).trim()
      }
    }
  }
  return null
}

// Computed property: Check if underlying cause data exists
const hasUnderlyingCauseData = computed(() => {
  return true // Always display Underlying Cause section
})

// Computed property: Get regulatory rule cue text
const regulatoryRuleCueText = computed(() => {
  // Use real data if available
  if (props.node?.explanation_composer?.regulatory_rule_cue) {
    return props.node.explanation_composer.regulatory_rule_cue
  }
  // Default text
  return "Vessels must reduce speed before entering controlled harbor zones and adjust heading to merge into inbound traffic lanes."
})

// Computed property: Get operational protocols text
const operationalProtocolsText = computed(() => {
  // Use real data if available
  if (props.node?.explanation_composer?.operational_protocol_rationale) {
    return props.node.explanation_composer.operational_protocol_rationale
  }
  // Default text
  return "Large tankers often perform a smooth decelerate–align maneuver prior to pilot boarding to stabilize motion and ensure predictable handling."
})

// Computed property: Get SD-KG support text for behavior
const sdkgSupportText = computed(() => {
  // Use real data if available
  if (props.node?.behavior_estimator?.graph_support) {
    return props.node.behavior_estimator.graph_support
  }
  // Default text
  return "Conditioned on Navigation status = Underway using engine and Vessel type = Tanker, the SD-KG estimates P(Port-Entry: Decelerate–Align) ≈ 0.58, which ranks 1st learned behavior patterns for this context."
})

// Computed property: Get contextual justification text
const contextualJustificationText = computed(() => {
  // Use real data if available
  if (props.node?.behavior_estimator?.contextual_justification) {
    return props.node.behavior_estimator.contextual_justification
  }
  // Default text
  return "The segment occurs at the harbor entrance where inbound vessels are expected to slow down and align to the designated lane."
})

// Computed property: Check if explanation data exists
const hasExplanationData = computed(() => {
  return hasSdkgSupport.value || true // Contextual Justification is always displayed
})

// Computed property: Filter static attributes
const filteredStaticAttributes = computed(() => {
  if (!props.node?.static_attributes) return []
  return props.node.static_attributes
})

// Format key for display (convert snake_case to Title Case)
const formatKey = (key) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// Computed property: Get current behavior title
const currentBehaviorTitle = computed(() => {
  const intent = props.node?.context?.current_behavior?.intent || "No intent data available"
  const bracketIndex = intent.indexOf('(')
  return bracketIndex !== -1 ? intent.substring(0, bracketIndex).trim() : intent
})

// Computed property: Get current behavior description
const currentBehaviorDescription = computed(() => {
  const intent = props.node?.context?.current_behavior?.intent || ""
  const bracketIndex = intent.indexOf('(')
  if (bracketIndex !== -1) {
    const afterBracket = intent.substring(bracketIndex)
    const description = afterBracket.replace(/^\(|\)$/g, '').trim()
    return description.startsWith(';') ? description.substring(1).trim() : description
  }
  return ""
})

// Computed property: Get previous behavior title
const previousBehaviorTitle = computed(() => {
  const intent = props.node?.context?.previous_behavior?.intent || "No intent data available"
  const bracketIndex = intent.indexOf('(')
  return bracketIndex !== -1 ? intent.substring(0, bracketIndex).trim() : intent
})

// Computed property: Get previous behavior description
const previousBehaviorDescription = computed(() => {
  const intent = props.node?.context?.previous_behavior?.intent || ""
  const bracketIndex = intent.indexOf('(')
  if (bracketIndex !== -1) {
    const afterBracket = intent.substring(bracketIndex)
    const description = afterBracket.replace(/^\(|\)$/g, '').trim()
    return description.startsWith(';') ? description.substring(1).trim() : description
  }
  return ""
})

// Computed property: Get next behavior title
const nextBehaviorTitle = computed(() => {
  const intent = props.node?.context?.next_behavior?.intent || "No intent data available"
  const bracketIndex = intent.indexOf('(')
  return bracketIndex !== -1 ? intent.substring(0, bracketIndex).trim() : intent
})

// Computed property: Get next behavior description
const nextBehaviorDescription = computed(() => {
  const intent = props.node?.context?.next_behavior?.intent || ""
  const bracketIndex = intent.indexOf('(')
  if (bracketIndex !== -1) {
    const afterBracket = intent.substring(bracketIndex)
    const description = afterBracket.replace(/^\(|\)$/g, '').trim()
    return description.startsWith(';') ? description.substring(1).trim() : description
  }
  return ""
})

// Computed property: Check if behavior details exist
const hasBehaviorDetails = computed(() => {
  return currentBehaviorDescription.value || previousBehaviorDescription.value || nextBehaviorDescription.value
})

// Computed property: Check if behavior data exists
const hasBehaviorData = computed(() => {
  return hasContextData.value || hasExplanationData.value || hasBehaviorDetails.value
})

// Computed property: Check if context data exists
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
const currentLevel = ref(2) // Default display level

// Performance configuration for graph rendering
const PERFORMANCE_CONFIG = {
  MAX_NODES: 1000,
  MAX_LINKS: 2000,
  NODE_RADIUS: 4,
  SIMULATION_QUALITY: 'medium'
}

// Animation configuration for graph interactions
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

// Highlight colors for interactive elements
const HIGHLIGHT_COLORS = {
  link: '#fbbf24',
  node: '#fbbf24',
  pulse: '#f59e0b'
}

// Node type definitions for legend display
const nodeTypes = ref([
  { name: 'behavior', label: 'Behavior', color: '#10b981' },
  { name: 'attribute', label: 'Attribute', color: '#f59e0b' },
  { name: 'function', label: 'Function', color: '#ef4444' },
  { name: 'trajectory', label: 'Trajectory', color: '#8b5cf6' },
  { name: 'segment', label: 'Segment', color: '#06b6d4' },
])

// Computed property: Get available graph levels
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

// Computed property: Check if graph data exists
const hasGraphData = computed(() => {
  return props.node.graph?.nodes && props.node.graph.nodes.length > 1
})

// Computed property: Filter nodes by current level
const filteredNodes = computed(() => {
  if (!hasGraphData.value) return []
  
  const allNodes = props.node.graph.nodes
  return allNodes.filter(node => node.level <= currentLevel.value && node.level > 0)
})

// Computed property: Filter links by current level
const filteredLinks = computed(() => {
  if (!props.node.graph?.links) return []
  
  return props.node.graph.links.filter(link => link.level <= currentLevel.value)
})

// Computed property: Filter nodes for expanded graph
const expandedFilteredNodes = computed(() => {
  if (!hasGraphData.value) return []
  
  const allNodes = props.node.graph.nodes
  return allNodes.filter(node => node.level <= expandedCurrentLevel.value && node.level > 0)
})

// Computed property: Filter links for expanded graph
const expandedFilteredLinks = computed(() => {
  if (!props.node.graph?.links) return []
  
  return props.node.graph.links.filter(link => link.level <= expandedCurrentLevel.value)
})

// Build graph data structure for force-graph library
const buildGraphData = (isExpanded = false) => {
  if (!hasGraphData.value) {
    return { nodes: [], links: [] }
  }

  // Create central node (current node)
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

  // Create related nodes based on level filtering
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

  // Create links between nodes
  const links = (isExpanded ? expandedFilteredLinks.value : filteredLinks.value)
    .map(link => ({ 
      source: link.source, 
      target: link.target,
      level: link.level 
    }))
    .filter(link => nodeById.has(link.source) && nodeById.has(link.target))

  // Build neighbor relationships for highlighting
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

// Debounce function for performance optimization
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

// Start pulse animation for highlighted nodes
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

// Stop pulse animation
function stopPulseAnimation() {
  if (pulseAnimationId) {
    cancelAnimationFrame(pulseAnimationId)
    pulseAnimationId = null
  }
}

// Get current pulse effect values
function getPulseEffect() {
  const pulse = Math.sin(pulseTime * 0.002) * 0.5 + 0.5
  return {
    radius: 2 + pulse * 2,
    opacity: 0.3 + pulse * 0.3
  }
}

// Highlight connected nodes in main graph
function highlightConnectedNodes(node) {
  if (!node) {
    highlightNodes = new Set()
    highlightLinks = new Set()
    draggedNode = null
    currentHighlightedNodeId.value = null
    return
  }

  const newNodes = new Set([node])
  const newLinks = new Set()
  
  node.links.forEach(l => newLinks.add(l))
  node.neighbors.forEach(n => newNodes.add(n))
  
  highlightNodes = newNodes
  highlightLinks = newLinks
  draggedNode = node
  currentHighlightedNodeId.value = node.id
  
  // Start pulse animation for visual feedback
  startPulseAnimation()
}

// Highlight connected nodes in expanded graph
function highlightExpandedConnectedNodes(node) {
  if (!node) {
    expandedHighlightNodes = new Set()
    expandedHighlightLinks = new Set()
    expandedDraggedNode = null
    currentHighlightedNodeId.value = null
    return
  }

  const newNodes = new Set([node])
  const newLinks = new Set()
  
  node.links.forEach(l => newLinks.add(l))
  node.neighbors.forEach(n => newNodes.add(n))
  
  expandedHighlightNodes = newNodes
  expandedHighlightLinks = newLinks
  expandedDraggedNode = node
  currentHighlightedNodeId.value = node.id
  
  startPulseAnimation()
}

// Clear highlight in main graph
function clearHighlight() {
  highlightNodes = new Set()
  highlightLinks = new Set()
  draggedNode = null
  currentHighlightedNodeId.value = null
}

// Clear highlight in expanded graph
function clearExpandedHighlight() {
  expandedHighlightNodes = new Set()
  expandedHighlightLinks = new Set()
  expandedDraggedNode = null
  currentHighlightedNodeId.value = null
}

// Clear all highlights in both graphs
const clearAllHighlights = () => {
  clearHighlight()
  if (isGraphExpanded.value) {
    clearExpandedHighlight()
  }
  stopPulseAnimation()
}

// ============================
// Text-to-Graph Highlight Functions
// ============================

// Highlight current behavior node when clicking on behavior text
const highlightCurrentBehavior = () => {
  const behaviorTitle = currentBehaviorTitle.value
  
  if (!behaviorTitle) return
  
  // Find behavior node by title
  const node = findNodeByTitle(behaviorTitle, 'behavior')
  if (node) {
    highlightSpecificNode(node)
    
    // Also highlight in expanded graph if open
    if (isGraphExpanded.value && expandedFg) {
      highlightSpecificNode(node, true)
    }
  } else {
    console.warn(`Behavior node not found: ${behaviorTitle}`)
    // Try to find any behavior node
    const anyBehaviorNode = findAnyBehaviorNode()
    if (anyBehaviorNode) {
      highlightSpecificNode(anyBehaviorNode)
      
      if (isGraphExpanded.value && expandedFg) {
        highlightSpecificNode(anyBehaviorNode, true)
      }
    }
  }
}

// Highlight attribute node when clicking on attribute text
const highlightAttribute = (item) => {
  // Parse attribute text
  const colonIndex = item.indexOf(':')
  if (colonIndex === -1) return
  
  const label = item.substring(0, colonIndex).trim()
  const value = item.substring(colonIndex + 1).trim()
  
  // Clean value (remove brackets and range markers)
  let cleanValue = value.replace(/\[.*?\)/g, '').trim()
  cleanValue = cleanValue.replace(/^location:\s*/i, '').trim()
  cleanValue = cleanValue.split(',')[0].trim()
  
  // Determine node type and search strategy
  let nodeType = 'attribute'
  let searchTerms = []
  
  // Build search terms based on attribute type
  switch(label.toLowerCase()) {
    case 'navigation status':
      searchTerms = [cleanValue, 'navigation', 'status', 'underway', 'engine']
      nodeType = 'attribute'
      break
    case 'hazardous cargo':
      searchTerms = [cleanValue === 'yes' ? 'hazardous' : 'non-hazardous', 'cargo', 'hazardous']
      nodeType = 'attribute'
      break
    case 'vessel type':
      searchTerms = [cleanValue, 'vessel', 'type', cleanValue.toLowerCase()]
      nodeType = 'trajectory'
      break
    case 'spatial context':
      searchTerms = [cleanValue, 'location', 'spatial', 'context']
      nodeType = 'attribute'
      break
    case 'draught':
    case 'length':
    case 'width':
      searchTerms = [label.toLowerCase(), cleanValue, 'dimension', 'measurement']
      nodeType = 'attribute'
      break
    default:
      searchTerms = [cleanValue, label.toLowerCase()]
  }
  
  // Try to find the node
  const node = findNodeBySearchTerms(searchTerms, nodeType, label, cleanValue)
  if (node) {
    highlightSpecificNode(node)
    
    if (isGraphExpanded.value && expandedFg) {
      highlightSpecificNode(node, true)
    }
  } else {
    console.warn(`Attribute node not found for: ${label}: ${cleanValue}`)
  }
}

// Highlight imputation function node
const highlightImputationFunction = () => {
  const functionName = functionNameText.value
  if (!functionName) return
  
  // Search for function node
  const node = findNodeByTitle(functionName, 'function')
  if (node) {
    highlightSpecificNode(node)
    
    if (isGraphExpanded.value && expandedFg) {
      highlightSpecificNode(node, true)
    }
  } else {
    // Try alternative search terms
    const searchTerms = ['linear interpolation', 'interpolation', 'imputation', 'function']
    const altNode = findNodeBySearchTerms(searchTerms, 'function', 'Imputation Function', functionName)
    if (altNode) {
      highlightSpecificNode(altNode)
      
      if (isGraphExpanded.value && expandedFg) {
        highlightSpecificNode(altNode, true)
      }
    } else {
      console.warn(`Imputation function node not found: ${functionName}`)
    }
  }
}

// Find any behavior node in the graph
const findAnyBehaviorNode = () => {
  if (!hasGraphData.value) return null
  
  const allNodes = props.node.graph.nodes
  return allNodes.find(node => node.type === 'behavior')
}

// Find node by title with optional type filter
const findNodeByTitle = (title, typeFilter = null) => {
  if (!hasGraphData.value) return null
  
  const allNodes = props.node.graph.nodes
  const cleanTitle = title.trim().toLowerCase()
  
  return allNodes.find(node => {
    // Filter by type if specified
    if (typeFilter && node.type !== typeFilter) return false
    
    // Try to match node's title or label
    const nodeTitle = node.title || node.label || ''
    const cleanNodeTitle = nodeTitle.trim().toLowerCase()
    
    // Exact match or contains match
    return cleanNodeTitle === cleanTitle || 
           cleanNodeTitle.includes(cleanTitle) || 
           cleanTitle.includes(cleanNodeTitle)
  })
}

// Find node by multiple search terms with scoring
const findNodeBySearchTerms = (searchTerms, expectedType, attributeLabel, attributeValue) => {
  if (!hasGraphData.value) return null
  
  const allNodes = props.node.graph.nodes
  
  // Score each node based on match quality
  const scoredNodes = allNodes.map(node => {
    const nodeTitle = (node.title || node.label || '').toLowerCase()
    const nodeType = node.type || ''
    
    let score = 0
    
    // Check type match
    if (expectedType && nodeType === expectedType) {
      score += 10
    }
    
    // Check each search term
    searchTerms.forEach(term => {
      if (nodeTitle.includes(term.toLowerCase())) {
        score += 5
      }
      if (nodeTitle === term.toLowerCase()) {
        score += 10 // Exact match bonus
      }
    })
    
    // Special handling for specific attributes
    if (attributeLabel.toLowerCase().includes('spatial') && nodeTitle.includes('location')) {
      score += 15
    }
    if (attributeLabel.toLowerCase().includes('vessel type') && nodeType === 'trajectory') {
      score += 20
    }
    
    return { node, score }
  })
  
  // Sort by score and return the best match
  scoredNodes.sort((a, b) => b.score - a.score)
  
  // Return the best match if it has a reasonable score
  if (scoredNodes.length > 0 && scoredNodes[0].score > 5) {
    return scoredNodes[0].node
  }
  
  return null
}

// Highlight specific node in graph
const highlightSpecificNode = (nodeData, isExpanded = false) => {
  if (isExpanded) {
    // Handle expanded graph
    const graph = expandedFg
    if (!graph || !nodeData) return
    
    // Get actual node object in the graph
    const graphNodes = graph.graphData().nodes
    const targetNode = graphNodes.find(n => n.id === nodeData.id)
    
    if (targetNode) {
      // Highlight the node and its connections
      highlightExpandedConnectedNodes(targetNode)
      
      // Auto-center on the node
      setTimeout(() => {
        if (expandedFg) {
          expandedFg.centerAt(targetNode.x, targetNode.y, 1000)
          expandedFg.zoom(1.5, 1000)
        }
      }, 100)
    }
  } else {
    // Handle main graph
    const graph = fg
    if (!graph || !nodeData) return
    
    const graphNodes = graph.graphData().nodes
    const targetNode = graphNodes.find(n => n.id === nodeData.id)
    
    if (targetNode) {
      highlightConnectedNodes(targetNode)
      
      // Auto-center on the node
      setTimeout(() => {
        if (fg) {
          fg.centerAt(targetNode.x, targetNode.y, 1000)
          fg.zoom(1.5, 1000)
        }
      }, 100)
    }
  }
}

// Initialize force graph with dynamic effects
function initForceGraph() {
  if (!graphEl.value) return

  if (fg) {
    fg.graphData({ nodes: [], links: [] })
    fg = null
  }

  // Physics simulation settings
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
    
    // Configure physics forces
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

        // Draw highlight background
        if (isHighlighted) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + 3, 0, 2 * Math.PI, false)
          ctx.fillStyle = `${HIGHLIGHT_COLORS.node}20`
          ctx.fill()
        }

        // Draw main node
        ctx.beginPath()
        ctx.arc(node.x, node.y, finalRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()

        // Draw labels at appropriate zoom levels
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
    
    // Add click event listeners for static attributes
    nextTick(() => {
      setupAttributeClickListeners()
    })
    
    console.log('✅ ForceGraph initialized for segment detail view')
    
  } catch (error) {
    console.error('❌ Failed to initialize ForceGraph:', error)
  }
}

// Setup click listeners for static attributes
const setupAttributeClickListeners = () => {
  const attrElements = document.querySelectorAll('.clickable-attr')
  attrElements.forEach(el => {
    el.addEventListener('click', (e) => {
      const attrLabel = e.target.getAttribute('data-attr')
      const attrValue = e.target.getAttribute('data-value')
      
      if (attrLabel && attrValue) {
        const item = `${attrLabel}: ${attrValue}`
        highlightAttribute(item)
      }
    })
  })
}

// Initialize expanded force graph for fullscreen view
function initExpandedForceGraph() {
  if (!expandedGraphEl.value) return

  if (expandedFg) {
    expandedFg.graphData({ nodes: [], links: [] })
    expandedFg = null
  }

  // Enhanced settings for expanded view
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

        // Draw highlight background
        if (isHighlighted) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + 5, 0, 2 * Math.PI, false)
          ctx.fillStyle = `${HIGHLIGHT_COLORS.node}30`
          ctx.fill()
        }

        // Draw main node
        ctx.beginPath()
        ctx.arc(node.x, node.y, finalRadius, 0, 2 * Math.PI, false)
        ctx.fillStyle = nodeColor
        ctx.fill()
        
        // Draw pulse effect for center node
        if (isCenter) {
          const pulse = getPulseEffect()
          ctx.beginPath()
          ctx.arc(node.x, node.y, finalRadius + pulse.radius * 1.5, 0, 2 * Math.PI, false)
          ctx.strokeStyle = `${HIGHLIGHT_COLORS.pulse}${Math.floor(pulse.opacity * 255).toString(16).padStart(2, '0')}`
          ctx.lineWidth = 3
          ctx.stroke()
        }

        // Draw labels (more detailed in expanded view)
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

// Configure physics forces for graph simulation
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

// Update main graph size based on container
function updateGraphSize() {
  if (!graphEl.value || !fg) return
  const rect = graphEl.value.getBoundingClientRect()
  fg.width(rect.width).height(rect.height)
}

// Update expanded graph size
function updateExpandedGraphSize() {
  if (!expandedGraphEl.value || !expandedFg) return
  const rect = expandedGraphEl.value.getBoundingClientRect()
  expandedFg.width(rect.width).height(rect.height)
}

// Resize handler with debouncing
const resizeHandler = debounce(() => {
  updateGraphSize()
  if (isGraphExpanded.value) {
    updateExpandedGraphSize()
  }
}, 200)

// Event handlers for graph interactions
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

// Get description for graph levels
const getLevelDescription = (level) => {
  const descriptions = {
    1: 'Direct connections',
    2: '2nd degree connections'
  }
  return descriptions[level] || `Level ${level}`
}

// Component emits definition
const emit = defineEmits(['open-node'])

// Lifecycle hooks
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

// Watchers for reactive updates
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
/* Two-column layout container */
.page-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* Left column: Main content area */
.main-content {
  flex: 1;
  min-width: 0; /* Prevent content overflow */
}

/* Right column: Knowledge graph sidebar */
.graph-sidebar {
  width: 400px;
  min-width: 400px;
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  margin-left: 20px;
  margin-right: -200px;
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

/* Main content area */
.body {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

/* Section styling */
.section-title {
  font-size: 30px !important;
  font-weight: 700 !important;
  margin: 24px 0 12px 0;
  color: #111827;
}

/* Bullet list styling */
.bullet-list {
  padding-left: 18px;
  margin: 12px 0 20px;
  font-size: 30px !important;
  color: #374151;
}

.bullet-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

/* Nested bullet list for indented content */
.nested-list {
  margin-left: 20px;
  margin-top: 8px;
  margin-bottom: 12px;
}

/* Section dividers */
.section-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 20px 0;
}

/* Attribute details styling */
.attribute-details {
  margin-left: 20px;
  margin-top: 4px;
  font-size: 0.9em;
  color: #666;
}

/* Clickable element styles */
.clickable-behavior,
.clickable-function {
  cursor: pointer;
  transition: all 0.2s ease;
  color: #3b82f6 !important;
}

.clickable-behavior:hover,
.clickable-function:hover {
  text-decoration: underline;
}

/* SD-KG highlight styling */
.sdkg-highlight {
  color: #dc2626 !important;
}

/* Graph section styles */
.graph-section {
  margin: 0;
  padding: 20px;
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

.graph-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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

/* Graph legend */
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

/* Expanded graph modal styles */
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

/* Global styles for clickable attributes */
:global(.clickable-attr) {
  cursor: pointer;
  transition: all 0.2s ease;
  color: #3b82f6 !important;
}

:global(.clickable-attr:hover) {
  text-decoration: underline;
}

/* Responsive design */
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
    font-size: 24px;
  }
  
  .section-title {
    font-size: 22px !important;
  }
  
  .bullet-list,
  .bullet-list li {
    font-size: 18px !important;
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

@media (max-width: 480px) {
  .graph-container {
    padding: 16px;
  }
  
  .graph-wrapper {
    height: 250px;
  }
  
  .legend-items {
    grid-template-columns: 1fr;
  }
  
  .graph-modal-title {
    font-size: 18px;
  }
  
  .section-title {
    font-size: 20px !important;
  }
  
  .bullet-list,
  .bullet-list li {
    font-size: 16px !important;
  }
}
</style>