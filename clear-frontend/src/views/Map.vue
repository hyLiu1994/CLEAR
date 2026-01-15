<template>
  <AppPageLayout>
    <section class="panel panel--fill">
      <!-- Enhanced header with decorative elements and gradient background -->
      <header class="panel-header">
        <!-- Decorative background elements -->
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
        
        <!-- Main title container -->
        <div class="title-container">
          <h1 class="title">
            Trajectory <span class="gradient-text">Visualization</span>
          </h1>
        </div>
        
        <!-- Header controls (loading indicator) -->
        <div class="header-controls">
          <div class="loading-indicator" v-if="loading">
            <span class="loading-spinner"></span>
            Loading...
          </div>
        </div>
      </header>

      <div class="panel-body">
        <div class="map-wrapper">
          <div ref="mapContainer" id="clear-map" class="map-container"></div>

          <!-- Reusable FloatingFilter component -->
          <FloatingFilter
            v-model="showFilter"
            title="Filter"
            @apply="applyFiltersDebounced"
            @reset="resetFilters"
          >
            <!-- Time range filter - Updated description -->
            <div class="field">
              <label class="field-label">Max Segment Duration (seconds)</label>
              <div class="field-row">
                <div class="sub-field">
                  <input
                    v-model.number="filters.maxTimeGap"
                    class="field-input"
                    type="number"
                    min="0"
                    step="60"
                    placeholder="e.g., 3600 (1 hour)"
                  />
                </div>
              </div>
              <div class="field-hint">
                Hide segments with total duration larger than this value
              </div>
            </div>

            <!-- MMSI multi-select dropdown -->
            <div class="field">
              <label class="field-label">MMSI</label>
              <div class="multi-select-wrapper">
                <div 
                  class="dropdown-trigger"
                  :class="{ 'dropdown-open': dropdowns.mmsi }"
                  @click="toggleDropdown('mmsi')"
                >
                  <span class="selected-text">
                    {{ getSelectedText('mmsi') }}
                  </span>
                  <span class="dropdown-arrow">▼</span>
                </div>
                
                <div v-if="dropdowns.mmsi" class="dropdown-menu">
                  <div class="search-box">
                    <input
                      v-model="searchQueries.mmsi"
                      type="text"
                      placeholder="Search MMSI..."
                      class="search-input"
                      @click.stop
                    />
                  </div>
                  
                  <div class="options-list">
                    <div
                      v-for="mmsi in getFilteredOptions('mmsi')"
                      :key="mmsi"
                      class="option-item"
                      :class="{ 'option-selected': filters.mmsi.includes(mmsi) }"
                      @click="toggleOption('mmsi', mmsi)"
                    >
                      <span class="checkmark" v-if="filters.mmsi.includes(mmsi)">✓</span>
                      <span class="option-label">{{ mmsi }}</span>
                    </div>
                  </div>
                  
                  <div class="dropdown-actions">
                    <button type="button" class="action-btn" @click="selectAll('mmsi')">
                      Select All
                    </button>
                    <button type="button" class="action-btn" @click="clearAll('mmsi')">
                      Clear
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Time range filter -->
            <div class="field">
              <label class="field-label">Time range (UTC)</label>
              <div class="field-row-time">
                <div class="sub-field">
                  <span class="sub-label">From</span>
                  <input
                    v-model="filters.startTime"
                    class="field-input"
                    type="datetime-local"
                  />
                </div>
                <div class="sub-field">
                  <span class="sub-label">To</span>
                  <input
                    v-model="filters.endTime"
                    class="field-input"
                    type="datetime-local"
                  />
                </div>
              </div>
            </div>

            <!-- Bounding box filter -->
            <div class="field">
              <label class="field-label">Bounding box (Lon / Lat)</label>
              <div class="field-row">
                <div class="sub-field">
                  <span class="sub-label">Min Lon</span>
                  <input
                    v-model.number="filters.minLon"
                    class="field-input"
                    type="number"
                    step="0.1"
                  />
                </div>
                <div class="sub-field">
                  <span class="sub-label">Max Lon</span>
                  <input
                    v-model.number="filters.maxLon"
                    class="field-input"
                    type="number"
                    step="0.1"
                  />
                </div>
              </div>
              <div class="field-row">
                <div class="sub-field">
                  <span class="sub-label">Min Lat</span>
                  <input
                    v-model.number="filters.minLat"
                    class="field-input"
                    type="number"
                    step="0.1"
                  />
                </div>
                <div class="sub-field">
                  <span class="sub-label">Max Lat</span>
                  <input
                    v-model.number="filters.maxLat"
                    class="field-input"
                    type="number"
                    step="0.1"
                  />
                </div>
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
              <h3 class="details-title">Segment Details</h3>
              <button class="sidebar-close-btn" @click="closeDetailsSidebar">
                <span>×</span>
              </button>
            </div>
            
            <div class="details-sidebar-content">
              <div v-if="currentSegmentId" class="segment-details">
                <div v-if="iframeLoading" class="iframe-loading-overlay">
                  <div class="loading-spinner"></div>
                  <p>Loading page...</p>
                </div>

                <iframe 
                  :src="detailPageUrl"
                  class="details-iframe"
                  frameborder="0"
                  @load="onIframeLoad"
                  @error="onIframeError"
                  :style="{ opacity: iframeLoading ? 0 : 1 }"
                ></iframe>
              </div>

              <div v-else class="no-details">
                Click on a trajectory segment to view details
              </div>
            </div>

            <div class="details-sidebar-footer">
              <!-- Changed from "Open in New Tab" to "Open" and updated click handler -->
              <button 
                class="open-full-btn"
                @click="openDetailsInCurrentTab"
                :disabled="!currentSegmentId"
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
import { onMounted, onBeforeUnmount, ref, reactive, computed, watch } from 'vue'
import { Map, NavigationControl, Popup } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import AppPageLayout from '../components/AppPageLayout.vue'
import FloatingFilter from '../components/FloatingFilter.vue'

// Template refs
const mapContainer = ref(null)
const mapRef = ref(null)
const sidebarRef = ref(null)

// Component state
const showFilter = ref(false)
const loading = ref(false)
const simplifyData = ref(true)

const showDetailsSidebar = ref(false)
const currentSegmentId = ref(null)
const iframeLoading = ref(false) 
const detailError = ref(null)

let iframeLoadTimeout = null

// Filter criteria
const filters = reactive({
  maxTimeGap: null,
  mmsi: [],
  startTime: '',
  endTime: '',
  minLon: '',
  maxLon: '',
  minLat: '',
  maxLat: ''
})

// Dropdown menu states
const dropdowns = reactive({
  mmsi: false
})

// Search queries for dropdowns
const searchQueries = reactive({
  mmsi: ''
})

// Trajectory data
const trajectories = ref([])
const allSegmentFeatures = ref([])
const currentSegmentFeatures = ref([])

// Map view state
const currentBounds = ref(null)
const currentZoom = ref(0)

// Hover state helpers
let hoveredTrajectoryId = null
let hoveredSegmentId = null

// Debouncing timeouts
let filterTimeout = null
let moveEndTimeout = null

// Sidebar resize and drag state
const sidebarPosition = reactive({
  x: 0, // Horizontal position from right
  y: 0, // Vertical position from top
  width: 800, // Default width
  height: '100%' // Default height (percentage or px)
})

// Store original sidebar position for resetting
const originalSidebarPosition = {
  x: 0,
  y: 0,
  width: 800,
  height: '100%'
}

const isResizing = ref(false)
const resizeDirection = ref(null)
const isDragging = ref(false)
const dragStartPos = reactive({ x: 0, y: 0 })

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
      visibility: 'hidden',
      pointerEvents: 'none'
    }
  } else {
    // When sidebar is visible, use its current position and size
    const baseStyle = {
      width: typeof sidebarPosition.width === 'number' ? `${sidebarPosition.width}px` : sidebarPosition.width,
      height: sidebarPosition.height,
      transform: `translate(${sidebarPosition.x}px, ${sidebarPosition.y}px)`,
      right: '0',
      opacity: '1',
      visibility: 'visible',
      pointerEvents: 'auto'
    }
    
    return baseStyle
  }
})

// Computed properties for filter options
const availableMmsi = computed(() => {
  const mmsiSet = new Set()
  trajectories.value.forEach(traj => {
    traj.segments.forEach(seg => {
      if (seg.vessel_id) {
        mmsiSet.add(seg.vessel_id)
      }
    })
  })
  return Array.from(mmsiSet).sort()
})

const detailPageUrl = computed(() => {
  if (!currentSegmentId.value) return ''
  // Add ?embed=true parameter to load the page without navigation bar
  return `/node/${currentSegmentId.value}?embed=true`
})

/**
 * Check if a segment has a time range larger than the specified maximum duration
 * @param {Object} segment - Segment object
 * @param {number} maxDurationSeconds - Maximum allowed duration in seconds
 * @returns {boolean} True if segment duration exceeds the maximum
 */
function hasLargeTimeRange(segment, maxDurationSeconds) {
  if (!maxDurationSeconds || !segment.start_ts || !segment.end_ts) {
    return false
  }
  
  const startTime = new Date(segment.start_ts).getTime()
  const endTime = new Date(segment.end_ts).getTime()
  const totalDurationSeconds = (endTime - startTime) / 1000
  
  return totalDurationSeconds > maxDurationSeconds
}

/**
 * Simplify trajectory coordinates using Douglas-Peucker algorithm
 * @param {Array} coordinates - Array of [lon, lat] coordinates
 * @param {number} tolerance - Simplification tolerance
 * @returns {Array} Simplified coordinates
 */
function simplifyTrajectory(coordinates, tolerance = 0.0001) {
  if (coordinates.length <= 2) return coordinates
  
  function douglasPeucker(points, tolerance) {
    if (points.length <= 2) return points
    
    let maxDistance = 0
    let index = 0
    const start = points[0]
    const end = points[points.length - 1]
    
    for (let i = 1; i < points.length - 1; i++) {
      const distance = perpendicularDistance(points[i], start, end)
      if (distance > maxDistance) {
        maxDistance = distance
        index = i
      }
    }
    
    if (maxDistance > tolerance) {
      const left = douglasPeucker(points.slice(0, index + 1), tolerance)
      const right = douglasPeucker(points.slice(index), tolerance)
      return left.slice(0, -1).concat(right)
    } else {
      return [start, end]
    }
  }
  
  function perpendicularDistance(point, lineStart, lineEnd) {
    const [x, y] = point
    const [x1, y1] = lineStart
    const [x2, y2] = lineEnd
    
    const A = x - x1
    const B = y - y1
    const C = x2 - x1
    const D = y2 - y1
    
    const dot = A * C + B * D
    const lenSq = C * C + D * D
    let param = -1
    
    if (lenSq !== 0) param = dot / lenSq
    
    let xx, yy
    
    if (param < 0) {
      xx = x1
      yy = y1
    } else if (param > 1) {
      xx = x2
      yy = y2
    } else {
      xx = x1 + param * C
      yy = y1 + param * D
    }
    
    const dx = x - xx
    const dy = y - yy
    return Math.sqrt(dx * dx + dy * dy)
  }
  
  return douglasPeucker(coordinates, tolerance)
}

/**
 * Get simplification tolerance based on current zoom level
 * @param {number} zoom - Current map zoom level
 * @returns {number} Simplification tolerance value
 */
function getSimplificationTolerance(zoom) {
  if (zoom < 5) return 0.01
  if (zoom < 8) return 0.001
  if (zoom < 12) return 0.0001
  return 0.00001
}

/**
 * Check if a point is within specified bounds
 * @param {Array} point - [longitude, latitude] coordinates
 * @param {Array} bounds - Bounding box [[swLng, swLat], [neLng, neLat]]
 * @returns {boolean} True if point is within bounds
 */
function isPointInBounds(point, bounds) {
  const [lng, lat] = point
  const [[swLng, swLat], [neLng, neLat]] = bounds
  return lng >= swLng && lng <= neLng && lat >= swLat && lat <= neLat
}

/**
 * Check if any point of a line is within specified bounds
 * @param {Array} coordinates - Array of [lon, lat] coordinates
 * @param {Array} bounds - Bounding box [[swLng, swLat], [neLng, neLat]]
 * @returns {boolean} True if any point is within bounds
 */
function isLineInBounds(coordinates, bounds) {
  return coordinates.some(coord => isPointInBounds(coord, bounds))
}

// Multi-select dropdown methods
const toggleDropdown = (type) => {
  Object.keys(dropdowns).forEach(key => {
    if (key !== type) {
      dropdowns[key] = false
    }
  })
  dropdowns[type] = !dropdowns[type]
  
  if (dropdowns[type]) {
    searchQueries.mmsi = ''
  }
}

const getSelectedText = (type) => {
  const selected = filters[type]
  if (selected.length === 0) {
    return `Select ${type}`
  }
  if (selected.length === 1) {
    return selected[0]
  }
  return `${selected.length} selected`
}

const getFilteredOptions = (type) => {
  if (type === 'mmsi' && searchQueries.mmsi) {
    const query = searchQueries.mmsi.toLowerCase()
    return availableMmsi.value.filter(mmsi => 
      mmsi.toLowerCase().includes(query)
    )
  }
  if (type === 'mmsi') return availableMmsi.value
  return []
}

const toggleOption = (type, value) => {
  const selected = filters[type]
  if (selected.includes(value)) {
    const index = selected.indexOf(value)
    selected.splice(index, 1)
  } else {
    selected.push(value)
  }
}

const selectAll = (type) => {
  if (type === 'mmsi') {
    filters.mmsi = [...availableMmsi.value]
  }
}

const clearAll = (type) => {
  filters[type] = []
}

/**
 * Open the details sidebar for a specific segment
 * @param {string} segmentId - ID of the segment to display
 */
const openDetailsSidebar = (segmentId) => {
  console.log('Opening details sidebar for segment:', segmentId)

  detailError.value = null
  currentSegmentId.value = segmentId
 
  if (iframeLoadTimeout) {
    clearTimeout(iframeLoadTimeout)
    iframeLoadTimeout = null
  }

  // Reset sidebar position to default if it was previously moved/resized
  if (sidebarPosition.x !== originalSidebarPosition.x || 
      sidebarPosition.y !== originalSidebarPosition.y ||
      sidebarPosition.width !== originalSidebarPosition.width) {
    resetSidebarPosition()
  }

  showDetailsSidebar.value = true

  iframeLoading.value = true

  iframeLoadTimeout = setTimeout(() => {
    if (iframeLoading.value) {
      console.warn('Iframe loading timeout for:', detailPageUrl.value)
      detailError.value = 'Page loading timeout. The page may not exist or is taking too long to load.'
      iframeLoading.value = false
    }
  }, 8000)
}

/**
 * Close the details sidebar and reset its position
 */
const closeDetailsSidebar = () => {
  showDetailsSidebar.value = false
  currentSegmentId.value = null
  detailError.value = null
  iframeLoading.value = false

  // Reset sidebar position to default
  resetSidebarPosition()

  if (iframeLoadTimeout) {
    clearTimeout(iframeLoadTimeout)
    iframeLoadTimeout = null
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
 * Open the details page in the current browser tab (replaces iframe navigation)
 */
const openDetailsInCurrentTab = () => {
  if (currentSegmentId.value) {
    // Navigate to the details page in the current tab
    // Note: This will open the page without embed parameter, showing full navigation
    window.location.href = `/node/${currentSegmentId.value}`
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

  if (iframeLoadTimeout) {
    clearTimeout(iframeLoadTimeout)
    iframeLoadTimeout = null
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

  if (iframeLoadTimeout) {
    clearTimeout(iframeLoadTimeout)
    iframeLoadTimeout = null
  }
}

// Watch for changes to the detail page URL
watch(detailPageUrl, (newUrl, oldUrl) => {
  console.log('Iframe URL changed:', oldUrl, '->', newUrl)
  if (newUrl && newUrl !== oldUrl) {
    iframeLoading.value = true
  }
})

// Close dropdowns when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.multi-select-wrapper')) {
    Object.keys(dropdowns).forEach(key => {
      dropdowns[key] = false
    })
  }
}

// Debounced filter application
const applyFiltersDebounced = () => {
  if (filterTimeout) {
    clearTimeout(filterTimeout)
  }
  filterTimeout = setTimeout(() => {
    applyFilters()
  }, 300)
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

// Component lifecycle
onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await initMap()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  if (filterTimeout) clearTimeout(filterTimeout)
  if (moveEndTimeout) clearTimeout(moveEndTimeout)
  if (mapRef.value) {
    mapRef.value.remove()
    mapRef.value = null
  }

  if (iframeLoadTimeout) {
    clearTimeout(iframeLoadTimeout)
  }
})

/**
 * Initialize the map
 */
async function initMap() {
  const map = new Map({
    container: mapContainer.value || 'clear-map',
    style: {
      version: 8,
      sources: {
        'satellite-tiles': {
          type: 'raster',
          tiles: [
            'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          ],
          tileSize: 256,
          attribution:
            '© Esri, Maxar, Earthstar Geographics, and the GIS User Community'
        }
      },
      layers: [
        {
          id: 'satellite-tiles',
          type: 'raster',
          source: 'satellite-tiles'
        }
      ]
    },
    center: [9.7, 54.5],
    zoom: 8.5,
    pitch: 0,
    bearing: 0
  })

  mapRef.value = map
  map.addControl(new NavigationControl(), 'top-right')

  map.on('load', () => {
    // Add trajectory segments source
    map.addSource('trajectory-segments', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    })

    // Add trajectory line layer
    // Modified 2: Changed trajectory colors to blue scheme matching homepage
    map.addLayer({
      id: 'trajectory-segments-line',
      type: 'line',
      source: 'trajectory-segments',
      paint: {
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'hoverSegment'], false],
          5.0,
          ['boolean', ['feature-state', 'hoverTrajectory'], false],
          3.0,
          1.5
        ],
        'line-opacity': [
          'case',
          ['boolean', ['feature-state', 'hoverSegment'], false],
          1.0,
          ['boolean', ['feature-state', 'hoverTrajectory'], false],
          0.9,
          0.5
        ],
        'line-color': [
          'case',
          ['boolean', ['feature-state', 'hoverSegment'], false],
          '#3b82f6', // Bright blue for selected segment
          ['boolean', ['feature-state', 'hoverTrajectory'], false],
          '#60a5fa', // Medium blue for hovered trajectory
          '#93c5fd'  // Light blue for normal segments
        ]
      }
    })

    // Set up map interactions
    setupMapInteractions(map)
    
    // Listen to map move events for view-based loading
    map.on('moveend', () => {
      if (moveEndTimeout) clearTimeout(moveEndTimeout)
      moveEndTimeout = setTimeout(() => {
        currentBounds.value = map.getBounds().toArray()
        currentZoom.value = map.getZoom()
        updateMapData()
      }, 200)
    })

    currentBounds.value = map.getBounds().toArray()
    currentZoom.value = map.getZoom()
    
    // Load initial data
    loadInitialData()
  })
}

/**
 * Load initial trajectory data from backend
 */
async function loadInitialData() {
  loading.value = true
  try {
    const url = `http://localhost:8000/api/v1/trajectories?ts=${Date.now()}`
    const res = await fetch(url, { cache: 'no-store' })
    const data = await res.json()
    trajectories.value = data || []
    


    buildSegmentFeatures()
    updateMapData()
  } catch (err) {
    console.error('Failed to load trajectories from backend:', err)
    trajectories.value = []
  } finally {
    loading.value = false
  }
}

/**
 * Build GeoJSON features from trajectory data
 */
function buildSegmentFeatures() {
  allSegmentFeatures.value = []
  let featureIdCounter = 1

  trajectories.value.forEach(traj => {
    const sortedSegments = [...traj.segments].sort((a, b) => {
      return new Date(a.start_ts) - new Date(b.start_ts)
    })

    let previousEndPoint = null

    sortedSegments.forEach(seg => {
      // Check if segment has ID
      if (!seg.id) {
        seg.id = `segment_${featureIdCounter}`
      }
      
      // Apply time range filtering based on segment total duration
      if (filters.maxTimeGap !== null && filters.maxTimeGap !== undefined && filters.maxTimeGap >= 0) {
        if (hasLargeTimeRange(seg, filters.maxTimeGap)) {
          previousEndPoint = null
          return
        }
      }

      if (hasLargeJumps(seg.coordinates)) {
        console.log(`Skipping segment ${seg.id} due to large coordinate jumps`)
        previousEndPoint = null
        return
      }

      let coordinates = seg.coordinates || []
      if (simplifyData.value && coordinates.length > 10) {
        const tolerance = getSimplificationTolerance(currentZoom.value)
        coordinates = simplifyTrajectory(coordinates, tolerance)
      }

      if (previousEndPoint && coordinates.length > 0) {
        coordinates = [previousEndPoint, ...coordinates]
      }

      allSegmentFeatures.value.push({
        type: 'Feature',
        id: featureIdCounter++,
        properties: {
          trajectory_id: traj.id,
          segment_id: seg.id,
          vessel_id: seg.vessel_id || '',
          vessel_type: seg.vessel_type || '',
          summary: seg.summary || '',
          start_ts: seg.start_ts,
          end_ts: seg.end_ts,
          original_coordinates: seg.coordinates,
          duration_seconds: seg.start_ts && seg.end_ts ? 
            (new Date(seg.end_ts).getTime() - new Date(seg.start_ts).getTime()) / 1000 : 0,
          is_connected: previousEndPoint !== null
        },
        geometry: {
          type: 'LineString',
          coordinates: coordinates
        }
      })

      if (coordinates.length > 0) {
        previousEndPoint = coordinates[coordinates.length - 1]
      } else {
        previousEndPoint = null
      }
    })
  })
}

/**
 * Detect large jumps in segment coordinates (only check maximum distance)
 * @param {Array} coordinates - Array of [lon, lat] coordinates
 * @returns {boolean} True if large jumps are detected
 */
function hasLargeJumps(coordinates) {
  if (!coordinates || coordinates.length < 2) {
    return false
  }

  const MAX_JUMP_DISTANCE_KM = 5

  for (let i = 1; i < coordinates.length; i++) {
    const [lon1, lat1] = coordinates[i - 1]
    const [lon2, lat2] = coordinates[i]
    
    const distance = calculateDistance([lon1, lat1], [lon2, lat2])
    if (distance > MAX_JUMP_DISTANCE_KM) {
      return true
    }
  }

  return false
}

/**
 * Calculate distance between two coordinates in kilometers using Haversine formula
 * @param {Array} coord1 - [longitude, latitude] of first point
 * @param {Array} coord2 - [longitude, latitude] of second point
 * @returns {number} Distance in kilometers
 */
function calculateDistance(coord1, coord2) {
  const [lon1, lat1] = coord1
  const [lon2, lat2] = coord2
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

/**
 * Update map data with current filtered features
 */
function updateMapData() {
  const map = mapRef.value
  if (!map || !map.getSource('trajectory-segments')) return

  let filteredFeatures = filterFeatures(allSegmentFeatures.value)

  if (currentBounds.value) {
    filteredFeatures = filteredFeatures.filter(feature => 
      isLineInBounds(feature.geometry.coordinates, currentBounds.value)
    )
  }

  currentSegmentFeatures.value = filteredFeatures

  const geojson = {
    type: 'FeatureCollection',
    features: currentSegmentFeatures.value
  }

  map.getSource('trajectory-segments').setData(geojson)
  clearHoverState(map)
}

/**
 * Filter features based on current filter criteria
 * @param {Array} features - Array of GeoJSON features
 * @returns {Array} Filtered features
 */
function filterFeatures(features) {
  const noFilter =
    !filters.maxTimeGap &&
    filters.mmsi.length === 0 &&
    !filters.startTime &&
    !filters.endTime &&
    filters.minLon === '' &&
    filters.maxLon === '' &&
    filters.minLat === '' &&
    filters.maxLat === ''

  if (noFilter) {
    return features
  }

  const startMillis = filters.startTime ? Date.parse(filters.startTime) : null
  const endMillis = filters.endTime ? Date.parse(filters.endTime) : null

  return features.filter(f => {
    const p = f.properties || {}

    if (filters.mmsi.length > 0 && !filters.mmsi.includes(String(p.vessel_id))) {
      return false
    }

    if (startMillis || endMillis) {
      const segStart = p.start_ts ? Date.parse(p.start_ts) : null
      const segEnd = p.end_ts ? Date.parse(p.end_ts) : null

      if (startMillis && segEnd && segEnd < startMillis) return false
      if (endMillis && segStart && segStart > endMillis) return false
    }

    if (
      filters.minLon !== '' ||
      filters.maxLon !== '' ||
      filters.minLat !== '' ||
      filters.maxLat !== ''
    ) {
      const [minLon, maxLon, minLat, maxLat] = [
        filters.minLon,
        filters.maxLon,
        filters.minLat,
        filters.maxLat
      ]

      const coords = f.geometry.coordinates || []
      const inBox = coords.some(([lon, lat]) => {
        if (minLon !== '' && lon < minLon) return false
        if (maxLon !== '' && lon > maxLon) return false
        if (minLat !== '' && lat < minLat) return false
        if (maxLat !== '' && lat > maxLat) return false
        return true
      })

      if (!inBox) return false
    }

    return true
  })
}

/**
 * Set up map interaction handlers
 * @param {Object} map - MapLibre map instance
 */
function setupMapInteractions(map) {
  if (!map) return

  map.on('mouseenter', 'trajectory-segments-line', () => {
    map.getCanvas().style.cursor = 'pointer'
  })

  map.on('mouseleave', 'trajectory-segments-line', () => {
    map.getCanvas().style.cursor = ''
    clearHoverState(map)
  })

  map.on('mousemove', 'trajectory-segments-line', e => {
    const features = map.queryRenderedFeatures(e.point, {
      layers: ['trajectory-segments-line']
    })
    
    if (!features.length) {
      clearHoverState(map)
      return
    }

    const feature = features[0]
    const props = feature.properties || {}
    const trajId = props.trajectory_id
    const segId = props.segment_id

    if (trajId === hoveredTrajectoryId && segId === hoveredSegmentId) {
      return
    }

    clearHoverState(map)

    hoveredTrajectoryId = trajId
    hoveredSegmentId = segId

    currentSegmentFeatures.value
      .filter(f => f.properties.trajectory_id === trajId)
      .forEach(f => {
        try {
          map.setFeatureState(
            { source: 'trajectory-segments', id: f.id },
            {
              hoverTrajectory: true,
              hoverSegment: f.properties.segment_id === segId
            }
          )
        } catch (error) {
          console.debug('Feature state error:', error)
        }
      })
  })

  // Click segment to show popup with details
  map.on('click', 'trajectory-segments-line', e => {
    const features = map.queryRenderedFeatures(e.point, {
      layers: ['trajectory-segments-line']
    })
    
    if (!features.length) return

    const feature = features[0]
    const props = feature.properties || {}
    const summary = props.summary || 'No summary available.'
    const trajectoryId = props.trajectory_id || 'Unknown trajectory'
    const segmentId = props.segment_id || 'Unknown segment'
    const vesselId = props.vessel_id || 'Unknown vessel'
    const duration = props.duration_seconds ? 
      `${Math.round(props.duration_seconds)} seconds` : ''

    const type = extractFirstWord(summary)

    const html = `
  <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 12px; max-width: 280px; color: #374151; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 12px 16px;">
      <div style="font-size: 13px; font-weight: 700; color: white; letter-spacing: 0.3px;">Segment: ${segmentId}</div>
    </div>

    <div style="padding: 16px; background: #ffffff;">
      <div style="display: grid; gap: 10px;">
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #6b7280; font-size: 11px; font-weight: 500;">Trajectory ID:</span>
          <span style="font-weight: 600; font-size: 11px; color: #111827;">${trajectoryId}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #6b7280; font-size: 11px; font-weight: 500;">Vessel ID:</span>
          <span style="font-weight: 600; font-size: 11px; color: #111827;">${vesselId}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #6b7280; font-size: 11px; font-weight=500;">Duration:</span>
          <span style="font-weight: 600; font-size: 11px; color: #111827;">${duration}</span>
        </div>
      </div>
      
      <div style="margin-top: 16px;">
        <a href="/node/${segmentId}" 
          style="display: block; text-align: center;
                  background: #3b82f6; 
                  color: white; 
                  padding: 8px 0; 
                  border-radius: 6px; 
                  text-decoration: none; 
                  font-weight: 600;
                  font-size: 11px;
                  transition: background-color 0.2s;"
          onmouseover="this.style.background='#2563eb';" 
          onmouseout="this.style.background='#3b82f6';">
          View Details
        </a>
      </div>
    </div>
  </div>
  `

    new Popup({ 
      closeButton: true, 
      closeOnClick: true,
      maxWidth: '500px',
      anchor: 'bottom',
      className: 'no-border-popup' 
    })
      .setLngLat(e.lngLat)
      .setHTML(html)
      .addTo(map)

    if (segmentId && segmentId !== 'Unknown segment') {
      console.log('Opening sidebar with segment ID:', segmentId)
      openDetailsSidebar(segmentId)
    } else {
      console.warn('No valid segment ID found to open sidebar')
    }
  })

  // Click on map background to close filter
  map.on('click', e => {
    const features = map.queryRenderedFeatures(e.point, {
      layers: ['trajectory-segments-line']
    })
    if (!features.length && showFilter.value) {
      showFilter.value = false
    }
  })
}

/**
 * Extract the first word from text
 * @param {string} text - Input text
 * @returns {string} First word or 'Unknown'
 */
function extractFirstWord(text) {
  if (!text || text === 'No summary available.') {
    return 'Unknown'
  }

  const firstWord = text.trim().split(/\s+/)[0]

  return firstWord || 'Unknown'
}

/**
 * Clear hover state from all features
 * @param {Object} map - MapLibre map instance
 */
function clearHoverState(map) {
  if (!currentSegmentFeatures.value || currentSegmentFeatures.value.length === 0) return
  
  currentSegmentFeatures.value.forEach(f => {
    try {
      map.setFeatureState(
        { source: 'trajectory-segments', id: f.id },
        { hoverTrajectory: false, hoverSegment: false }
      )
    } catch (error) {
      console.debug('Feature state error on clear:', error)
    }
  })
  
  hoveredTrajectoryId = null
  hoveredSegmentId = null
}

/**
 * Apply filters and update map
 */
function applyFilters() {
  buildSegmentFeatures()
  updateMapData()
  showFilter.value = false
}

/**
 * Reset all filters to default values
 */
function resetFilters() {
  filters.maxTimeGap = null
  filters.mmsi = []
  filters.startTime = ''
  filters.endTime = ''
  filters.minLon = ''
  filters.maxLon = ''
  filters.minLat = ''
  filters.maxLat = ''

  buildSegmentFeatures()
  updateMapData()
}

// Watch for performance option changes
watch([simplifyData], () => {
  if (mapRef.value && trajectories.value.length > 0) {
    buildSegmentFeatures()
    updateMapData()
  }
})

// Watch for time gap filter changes
watch(() => filters.maxTimeGap, () => {
  if (mapRef.value && trajectories.value.length > 0) {
    buildSegmentFeatures()
    updateMapData()
  }
})
</script>

<style scoped>
/* Main panel container with improved visual hierarchy */
.panel {
  width: 100%;
  border-radius: 16px; /* Modern rounded corners */
  background: #ffffff; /* Clean white background */
  box-shadow: 0 0 0 1px rgba(226, 232, 240, 0.8), 0 20px 40px rgba(15, 23, 42, 0.1); /* Softer shadow */
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Ensure content stays within rounded corners */
}

.panel--fill {
  flex: 1;
}

/* Enhanced panel header with gradient background and decorative elements */
.panel-header {
  padding: 2.5rem 2rem 1.5rem 2rem; /* Generous padding */
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); /* Subtle gradient background */
  border-bottom: 1px solid #e2e8f0; /* Soft border color */
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
  flex: 1; /* Take available space */
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

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem; /* Slightly larger for readability */
  color: #64748b; /* Softer gray */
  font-weight: 500;
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.panel-body {
  flex: 1;
  padding: 1.5rem; /* Increased padding for better spacing */
  box-sizing: border-box;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); /* Gradient background matching homepage */
  display: flex;
}

.map-wrapper {
  position: relative;
  flex: 1;
  border-radius: 12px; /* Larger radius */
  border: 1px solid #e2e8f0; /* Softer border */
  background: #ffffff; /* Clean white background */
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06); /* Subtle shadow */
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 12px; /* Match wrapper radius */
  overflow: hidden;
}

.field {
  margin-bottom: 12px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #475569; /* Better contrast */
}

.field-row {
  display: flex;
  gap: 8px;
}

.field-row-time {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sub-field {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sub-label {
  font-size: 12px;
  color: #64748b; /* Softer gray */
  margin-bottom: 3px;
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 8px; /* Consistent rounded corners */
  border: 1px solid #cbd5e1; /* Softer border */
  background: #ffffff; /* White background */
  padding: 8px 10px; /* Comfortable padding */
  font-size: 14px;
  color: #1e293b; /* Dark text for readability */
  outline: none;
  transition: all 0.2s ease;
}

.field-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.field-hint {
  font-size: 11px;
  color: #64748b; /* Softer gray */
  margin-top: 4px;
  font-style: normal; /* Remove italic for better readability */
}

.performance-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #475569; /* Better contrast */
}

.checkbox-input {
  margin: 0;
}

.checkbox-text {
  user-select: none;
}

/* Multi-select dropdown styles */
.multi-select-wrapper {
  position: relative;
  width: 100%;
}

.dropdown-trigger {
  width: 100%;
  padding: 8px 10px;
  max-width: 300px;
  border-radius: 8px; /* Consistent rounded corners */
  border: 1px solid #cbd5e1; /* Softer border */
  background: #ffffff; /* White background */
  color: #1e293b; /* Dark text */
  font-size: 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.dropdown-trigger:hover {
  border-color: #94a3b8;
}

.dropdown-trigger.dropdown-open {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.selected-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-arrow {
  font-size: 10px;
  transition: transform 0.2s;
  color: #64748b; /* Subtle gray */
}

.dropdown-trigger.dropdown-open .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #ffffff; /* White background */
  border: 1px solid #cbd5e1; /* Softer border */
  border-radius: 8px;
  margin-top: 4px;
  z-index: 1000;
  max-height: 200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* Subtle shadow */
}

.search-box {
  padding: 8px;
  border-bottom: 1px solid #e2e8f0; /* Light border */
}

.search-input {
  width: 100%;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #1e293b;
  font-size: 12px;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.options-list {
  flex: 1;
  overflow-y: auto;
  max-height: 120px;
}

.option-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
  font-size: 12px;
  color: #1e293b;
}

.option-item:hover {
  background: #f1f5f9; /* Light gray hover */
}

.option-item.option-selected {
  background: rgba(59, 130, 246, 0.1); /* Light blue background */
  color: #1d4ed8; /* Darker blue text */
}

.checkmark {
  color: #10b981; /* Green checkmark */
  font-weight: bold;
  width: 16px;
  display: flex;
  justify-content: center;
}

.option-label {
  flex: 1;
}

.dropdown-actions {
  padding: 8px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #475569;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

:deep(.maplibregl-control-container) {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.details-sidebar {
  position: absolute;
  top: 0;
  background: white;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  border-left: 1px solid #e5e7eb;
  border-radius: 8px 0 0 8px;
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
  right: 0;
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}

.details-sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
  border-radius: 8px 0 0 0;
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
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  font-size: 24px;
  line-height: 1;
  padding: 0;
  transition: all 0.2s;
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

.segment-details {
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
  transition: opacity 0.3s ease;
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
}

.iframe-loading-overlay .loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.iframe-loading-overlay p {
  margin: 0;
  font-weight: 500;
}

.no-details {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
  font-style: normal; /* Remove italic for better readability */
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.details-sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 0 0 0 8px;
}

.open-full-btn {
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); /* Gradient button */
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.open-full-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
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

:deep(.no-border-popup .maplibregl-popup-content) {
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  position: relative;
}

:deep(.no-border-popup .maplibregl-popup-tip) {
  display: none !important;
}

:deep(.no-border-popup .maplibregl-popup-content) {
  position: relative;
}
:deep(.no-border-popup .maplibregl-popup-content::after) {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid white;
  z-index: 1;
  filter: drop-shadow(0 2px 2px rgba(0, 0, 0, 0.2));
}
:deep(.no-border-popup .maplibregl-popup-close-button) {
  font-size: 18px !important;        
  color: white !important;
  background: none !important;       
  border-radius: 0 !important;       
  width: auto !important;           
  height: auto !important;          
  min-width: 20px !important;       
  min-height: 20px !important;       
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  right:0px !important;             
  top: 8px !important;               
  padding: 0 !important;
  margin: 0 !important;
  line-height: 1 !important;
  transition: all 0.2s !important;
  border: none !important;
  outline: none !important;
  cursor: pointer !important;
  z-index: 1000 !important;
  font-weight: 300 !important;       
  opacity: 0.9 !important;           
}

:deep(.no-border-popup .maplibregl-popup-close-button:hover) {
  opacity: 1 !important;
  transform: scale(1.2) !important;  
  color: #f8fafc !important;        
}

:deep(.no-border-popup .maplibregl-popup-content) {
  position: relative;
}

:deep(.no-border-popup .maplibregl-popup-content > div) {
  padding-top: 8px; 
  position: relative;
}

/* Responsive design adjustments */
@media (max-width: 1024px) {
  .title {
    font-size: 2rem; /* Slightly smaller on tablets */
  }
  
  .subtitle {
    font-size: 1rem; /* Adjust subtitle size */
  }
  
  .panel-header {
    padding: 2rem 1.5rem 1.25rem 1.5rem; /* Adjust padding */
  }
  
  .panel-body {
    padding: 1.25rem; /* Adjust padding */
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 1.75rem; /* Smaller for mobile */
  }
  
  .subtitle {
    font-size: 0.875rem; /* Smaller subtitle */
  }
  
  .panel-header {
    padding: 1.5rem 1rem 1rem 1rem; /* Compact padding */
    flex-direction: column; /* Stack title and controls */
    gap: 1rem;
  }
  
  .title-container {
    width: 100%;
  }
  
  .header-controls {
    align-self: flex-start; /* Align controls to left */
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
  
  .dropdown-trigger {
    max-width: none; /* Full width on mobile */
  }
}

@media (max-width: 480px) {
  .title {
    font-size: 1.5rem; /* Even smaller for very small screens */
  }
  
  .subtitle {
    font-size: 0.75rem; /* Very small subtitle */
  }
  
  .panel {
    border-radius: 12px; /* Smaller radius on mobile */
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