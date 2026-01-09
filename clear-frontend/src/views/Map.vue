<template>
  <AppPageLayout>
    <section class="panel panel--fill">
      <header class="panel-header">
        <div>
          <h2 class="section-title">Trajectory Visualization</h2>
        </div>
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
            <!-- Performance options 
            <div class="field">
              <label class="field-label">Performance Options</label>
              <div class="performance-options">
                <label class="checkbox-label">
                  <input
                    v-model="viewBasedLoading"
                    type="checkbox"
                    class="checkbox-input"
                  />
                  <span class="checkbox-text">Load visible area only</span>
                </label>
              </div>
            </div>
            -->
          </FloatingFilter>
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

// Component state
const showFilter = ref(false)
const loading = ref(false)
const simplifyData = ref(true) // Whether to simplify trajectory data
const viewBasedLoading = ref(false) // Whether to load only visible area

// Filter criteria
const filters = reactive({
  maxTimeGap: null, // Maximum segment duration in seconds
  mmsi: [], // Selected MMSI values
  startTime: '', // Start time for time range filter
  endTime: '', // End time for time range filter
  minLon: '', // Minimum longitude for bounding box
  maxLon: '', // Maximum longitude for bounding box
  minLat: '', // Minimum latitude for bounding box
  maxLat: '' // Maximum latitude for bounding box
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
const trajectories = ref([]) // Raw trajectory data from backend
const allSegmentFeatures = ref([]) // All segment features for filtering
const currentSegmentFeatures = ref([]) // Currently displayed segment features

// Map view state
const currentBounds = ref(null) // Current map bounds
const currentZoom = ref(0) // Current map zoom level

// Hover state helpers
let hoveredTrajectoryId = null
let hoveredSegmentId = null

// Debouncing timeouts
let filterTimeout = null
let moveEndTimeout = null

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

/**
 * Check if segment total duration exceeds the specified threshold
 * @param {Object} segment - The segment object with start_ts and end_ts
 * @param {number} maxDurationSeconds - Maximum allowed segment duration in seconds
 * @returns {boolean} True if segment duration exceeds threshold
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
 * Get simplification tolerance based on zoom level
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
 * Check if a point is within the specified bounds
 * @param {Array} point - [lng, lat] coordinates
 * @param {Array} bounds - [[swLng, swLat], [neLng, neLat]] bounds
 * @returns {boolean} True if point is within bounds
 */
function isPointInBounds(point, bounds) {
  const [lng, lat] = point
  const [[swLng, swLat], [neLng, neLat]] = bounds
  return lng >= swLng && lng <= neLng && lat >= swLat && lat <= neLat
}

/**
 * Check if a line has any points within the specified bounds
 * @param {Array} coordinates - Array of [lng, lat] coordinates
 * @param {Array} bounds - [[swLng, swLat], [neLng, neLat]] bounds
 * @returns {boolean} True if line intersects with bounds
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
    center: [10, 56],
    zoom: 5,
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
          '#ff4b3a',
          ['boolean', ['feature-state', 'hoverTrajectory'], false],
          '#ff9b7a',
          '#ffb199'
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
        if (viewBasedLoading.value && trajectories.value.length > 0) {
          updateMapData()
        }
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
    
    // === 最简单修改：只有这5行 ===
    if (trajectories.value.length > 0 && mapRef.value) {
      // 直接使用第一条轨迹的第一个点作为中心（最简单的实现）
      const firstTraj = trajectories.value[0]
      if (firstTraj.segments?.[0]?.coordinates?.[0]) {
        const firstPoint = firstTraj.segments[0].coordinates[0]
        mapRef.value.setCenter(firstPoint)
        mapRef.value.setZoom(5) // 设置一个合适的缩放级别
      }
    }
    // === 结束修改 ===

    // Build segment features for map display
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
    // Sort segments by start time to ensure proper connection order
    const sortedSegments = [...traj.segments].sort((a, b) => {
      return new Date(a.start_ts) - new Date(b.start_ts)
    })

    let previousEndPoint = null

    sortedSegments.forEach(seg => {
      // Apply time range filtering based on segment total duration
      if (filters.maxTimeGap !== null && filters.maxTimeGap !== undefined && filters.maxTimeGap >= 0) {
        // Skip segment if its total duration exceeds the threshold
        if (hasLargeTimeRange(seg, filters.maxTimeGap)) {
          previousEndPoint = null // Reset connection point when skipping a segment
          return
        }
      }

      // Check for abnormal jumps in segment coordinates (max distance between points)
      if (hasLargeJumps(seg.coordinates)) {
        console.log(`Skipping segment ${seg.id} due to large coordinate jumps`)
        previousEndPoint = null // Reset connection point when skipping a segment
        return
      }

      // Apply trajectory simplification
      let coordinates = seg.coordinates || []
      if (simplifyData.value && coordinates.length > 10) {
        const tolerance = getSimplificationTolerance(currentZoom.value)
        coordinates = simplifyTrajectory(coordinates, tolerance)
      }

      // Connect to previous segment if coordinates are available
      if (previousEndPoint && coordinates.length > 0) {
        // Always connect to previous segment without distance checking
        coordinates = [previousEndPoint, ...coordinates]
      }

      // Create segment feature with potentially connected coordinates
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

      // Update previous endpoint for next segment connection
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
    return false // Not enough points to check for jumps
  }

  const MAX_JUMP_DISTANCE_KM = 5 // Maximum allowed distance between consecutive points in km

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
  const R = 6371 // Earth's radius in kilometers
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

  // Filter features based on current criteria
  let filteredFeatures = filterFeatures(allSegmentFeatures.value)

  // Apply view-based filtering
  if (viewBasedLoading.value && currentBounds.value) {
    filteredFeatures = filteredFeatures.filter(feature => 
      isLineInBounds(feature.geometry.coordinates, currentBounds.value)
    )
  }

  currentSegmentFeatures.value = filteredFeatures

  const geojson = {
    type: 'FeatureCollection',
    features: currentSegmentFeatures.value
  }

  // Update map source data
  map.getSource('trajectory-segments').setData(geojson)
  
  // Clear hover state after data update
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

    // Time range filtering is already handled in buildSegmentFeatures

    // MMSI multi-select filter
    if (filters.mmsi.length > 0 && !filters.mmsi.includes(String(p.vessel_id))) {
      return false
    }

    // Time range filter
    if (startMillis || endMillis) {
      const segStart = p.start_ts ? Date.parse(p.start_ts) : null
      const segEnd = p.end_ts ? Date.parse(p.end_ts) : null

      if (startMillis && segEnd && segEnd < startMillis) return false
      if (endMillis && segStart && segStart > endMillis) return false
    }

    // Spatial bounding box filter
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

  // Cursor styling
  map.on('mouseenter', 'trajectory-segments-line', () => {
    map.getCanvas().style.cursor = 'pointer'
  })

  map.on('mouseleave', 'trajectory-segments-line', () => {
    map.getCanvas().style.cursor = ''
    clearHoverState(map)
  })

  // Hover highlighting for entire trajectory and current segment
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

    // Set feature state for all segments in the same trajectory
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
          // Ignore feature state errors - features might not be loaded yet
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
  <!-- Header -->
  <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 12px 16px;">
    <div style="font-size: 13px; font-weight: 700; color: white; letter-spacing: 0.3px;">Segment: ${segmentId}</div>
  </div>

  <!-- Basic Info -->
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
        <span style="color: #6b7280; font-size: 11px; font-weight: 500;">Duration:</span>
        <span style="font-weight: 600; font-size: 11px; color: #111827;">${duration}</span>
      </div>
    </div>
    
    <!-- Button -->
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
    new Popup({ closeButton: true, closeOnClick: true ,maxWidth: '500px',anchor: 'bottom' })
      .setLngLat(e.lngLat)
      .setHTML(html)
      .addTo(map)
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
      // Ignore feature state errors - features might not be loaded yet
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
watch([simplifyData, viewBasedLoading], () => {
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
/* Styles remain unchanged from original */
.panel {
  width: 100%;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e5e5e5, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

.panel--fill {
  flex: 1;
}

.panel-header {
  padding: 18px 22px 10px 22px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.section-title {
  font-size: 30px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.loading-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #e5e7eb;
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
  padding: 14px 22px 18px 22px;
  box-sizing: border-box;
  background: #f9fafb;
  display: flex;
}

.map-wrapper {
  position: relative;
  flex: 1;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
}

.field {
  margin-bottom: 12px;
}

.field-label {
  display: block;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #e5e7eb;
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
  font-size: 26px;
  color: #9ca3af;
  margin-bottom: 3px;
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.7);
  background: rgba(15, 23, 42, 0.9);
  padding: 7px 9px;
  font-size: 28px;
  color: #e5e7eb;
  outline: none;
}

.field-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.8);
}

.field-hint {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  font-style: italic;
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
  color: #e5e7eb;
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
  padding: 7px 9px;
  max-width: 300px;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.7);
  background: rgba(15, 23, 42, 0.9);
  color: #e5e7eb;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
}

.dropdown-trigger:hover {
  border-color: rgba(148, 163, 184, 0.9);
}

.dropdown-trigger.dropdown-open {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.8);
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
}

.dropdown-trigger.dropdown-open .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(148, 163, 184, 0.7);
  border-radius: 9px;
  margin-top: 4px;
  z-index: 1000;
  max-height: 200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-box {
  padding: 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
}

.search-input {
  width: 100%;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(31, 41, 55, 0.8);
  color: #e5e7eb;
  font-size: 12px;
  outline: none;
}

.search-input:focus {
  border-color: #3b82f6;
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
}

.option-item:hover {
  background: rgba(37, 99, 235, 0.2);
}

.option-item.option-selected {
  background: rgba(37, 99, 235, 0.3);
}

.checkmark {
  color: #10b981;
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
  border-top: 1px solid rgba(148, 163, 184, 0.3);
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(31, 41, 55, 0.8);
  color: #e5e7eb;
  font-size: 11px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background: rgba(55, 65, 81, 0.9);
}

:deep(.maplibregl-control-container) {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}



</style>