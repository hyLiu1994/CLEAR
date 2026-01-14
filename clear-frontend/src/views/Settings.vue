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
        
        <!-- Main title container -->
        <div class="title-container">
          <h1 class="title">
            Settings & 
            <span class="gradient-text">Pipeline Control</span>
          </h1>
        </div>
      </header>

      <div class="panel-body">
        <!-- Left: VISTA CONFIGURATION Only -->
        <div class="left">
          <!-- Expert Mode -->
          <section class="section">
            <h2 class="section-title">VISTA CONFIGURATION</h2>
            <p class="section-hint">
              Configure construction and imputation hyperparameters directly.
            </p>

            <div class="expert-group">
              <div class="expert-group-title">Dataset config</div>
              <div class="field-row">
                <label class="field-label">Trajectory number</label>
                <input
                  v-model.number="form.trajectoryNum"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Trajectory length</label>
                <input
                  v-model.number="form.trajectoryLen"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Minimal segment length</label>
                <input
                  v-model.number="form.miniSegmentLen"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>

            <div class="expert-group">
              <div class="expert-group-title">LLM config</div>
              <div class="field-row">
                <label class="field-label">API KEY</label>
                <input
                  v-model="form.apikey"  
                  type="text"               
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Platform</label>
                <select v-model="form.platform" class="field-input">
                  <option value="openai">OpenAI</option>
                  <option value="alibaba">Alibaba</option>
                </select>
              </div>
            </div>

            <div class="expert-group">
              <div class="expert-group-title">Concurrent config</div>
              <div class="field-row">
                <label class="field-label">Concurrent number</label>
                <input
                  v-model.number="form.concurrentNum"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Max retries</label>
                <input
                  v-model.number="form.maxRetries"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>

            <div class="expert-group">
              <div class="expert-group-title">SD-KG construction</div>
              <div class="field-row">
                <label class="field-label">Max retries</label>
                <input
                  v-model.number="form.retryTimes"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>

              <div class="field-row">
                <label class="field-label">Mining model</label>
                <select v-model="form.miningModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
              <div class="field-row">
                <label class="field-label">Coding model</label>
                <select v-model="form.codingModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
              <div class="field-row">
                <label class="field-label">e(f)</label>
                <input
                  v-model.number="form.eF"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>

            <div class="expert-group">
              <div class="expert-group-title">Imputation</div>
              <div class="field-row">
                <label class="field-label">Imputation model</label>
                <select v-model="form.imputationModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
              <div class="field-row">
                <label class="field-label">Top K</label>
                <input
                  v-model.number="form.topK"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>
          </section>
        </div>

        <!-- Right: Dataset + Pipeline Control -->
        <div class="right">
          <!-- Dataset Selection -->
          <section class="section">
            <h2 class="section-title">Dataset</h2>
            <p class="section-hint">
              Select which AIS dataset CLEAR should use as input for SD-KG construction and imputation.
            </p>
            <div class="field-row">
              <label class="field-label">Dataset</label>
              <select v-model="form.dataset" class="field-input">
                <option value="demo-dk">Demo · AIS-DK (subset)</option>
                <option value="demo-us">Demo · AIS-US (subset)</option>
                <option value="custom-dk">Custom · AIS-DK dataset</option>
                <option value="custom-us">Custom · AIS-US dataset</option>
              </select>
            </div>
            <!-- Information card -->
            <div v-if="isCustomDataset" class="custom-dataset-card">
              <div class="custom-dataset-header">
                <div class="custom-dataset-title">Custom Dataset Settings</div>
                <p class="custom-dataset-text">
                  {{ dateRangeHint }}
                </p>
              </div>
              <div class="field-row">
                <label class="field-label">Start Date</label>
                <input
                  v-model="form.startDate"
                  type="date"
                  :min="dateRange.min"
                  :max="dateRange.max"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">End Date</label>
                <input
                  v-model="form.endDate"
                  type="date"
                  :min="dateRange.min"
                  :max="dateRange.max"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Minimal time interval</label>
                <input
                  v-model.number="form.minTimeInterval"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
              <div class="field-row">
                <label class="field-label">Maximal time interval</label>
                <input
                  v-model.number="form.maxTimeInterval"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>
          </section>

          <section class="pipeline-section">
            <h2 class="section-title">Pipeline</h2>
            <p class="section-hint">
              Execute the SD-KG construction and trajectory imputation steps with the current configuration.
            </p>
            
            <!-- Build SD-KG -->
            <div class="pipeline-card">
              <div class="pipeline-header">
                <div>
                  <div class="pipeline-title">Build SD-KG</div>
                  <p class="pipeline-text">
                    Segment trajectories, extract patterns, and update the Structured Data-derived
                    Knowledge Graph based on the selected dataset and construction parameters.
                  </p>
                </div>
                <button
                  class="action-btn"
                  :disabled="sdkgStatus === 'running'"
                  @click="startSdkgBuild"
                >
                  {{ sdkgStatus === 'running' ? 'Running…' : 'Build SD-KG' }}
                </button>
              </div>

              <div class="progress-row">
                <div class="progress">
                  <div
                    class="progress-inner"
                    :style="{ width: sdkgProgress + '%' }"
                  ></div>
                </div>
                <div class="progress-label">
                  <span v-if="sdkgStatus === 'idle'">Idle</span>
                  <span v-else-if="sdkgStatus === 'running'">
                    Building SD-KG ({{ sdkgProgress }}%)
                  </span>
                  <span v-else>Completed · SD-KG updated</span>
                </div>
              </div>
            </div>

            <!-- Imputation -->
            <div class="pipeline-card">
              <div class="pipeline-header">
                <div>
                  <div class="pipeline-title">Run Imputation</div>
                  <p class="pipeline-text">
                    Use the current SD-KG and imputation model to fill missing segments in the
                    selected trajectories and attach explanations to each reconstructed gap.
                  </p>
                </div>
                <button
                  class="action-btn"
                  :disabled="imputeStatus === 'running' || sdkgStatus !== 'done'"
                  @click="startImputation"
                >
                  {{
                    imputeStatus === 'running'
                      ? 'Running…'
                      : sdkgStatus !== 'done'
                        ? 'Build SD-KG first'
                        : 'Run Imputation'
                  }}
                </button>
              </div>

              <div class="progress-row">
                <div class="progress">
                  <div
                    class="progress-inner"
                    :style="{ width: imputeProgress + '%' }"
                  ></div>
                </div>
                <div class="progress-label">
                  <span v-if="imputeStatus === 'idle'">Idle</span>
                  <span v-else-if="imputeStatus === 'running'">
                    Imputing trajectories ({{ imputeProgress }}%)
                  </span>
                  <span v-else>Completed · Missing segments imputed</span>
                </div>
              </div>
            </div>
            <div class="pipeline-card">
              <div class="pipeline-header">
                <div>
                  <div class="pipeline-title">Update CLEAR Content</div>
                  <p class="pipeline-text">
                    After completing SD-KG construction and trajectory imputation, update the CLEAR system 
                    with the latest results and make them available for visualization and analysis.
                  </p>
                </div>
                <button
                  class="action-btn"
                  :disabled="updateStatus === 'running' || sdkgStatus !== 'done' || imputeStatus !== 'done'"
                  @click="updateCLEARContent"
                >
                  {{
                    updateStatus === 'running'
                      ? 'Updating…'
                      : sdkgStatus !== 'done' || imputeStatus !== 'done'
                        ? 'Complete SD-KG & Impute first'
                        : 'Update CLEAR Content'
                  }}
                </button>
              </div>

              <div class="progress-row">
                <div class="progress">
                  <div
                    class="progress-inner"
                    :style="{ width: updateProgress + '%' }"
                  ></div>
                </div>
                <div class="progress-label">
                  <span v-if="updateStatus === 'idle'">Idle</span>
                  <span v-else-if="updateStatus === 'running'">
                    Updating CLEAR content ({{ updateProgress }}%)
                  </span>
                  <span v-else>Completed · CLEAR content updated</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { ref, onBeforeUnmount, computed } from 'vue'
import AppPageLayout from '../components/AppPageLayout.vue'

// New task ID for backend communication
const sdkgTaskId = ref(null)
const imputeTaskId = ref(null)
const updateTaskId = ref(null)

// Form data model containing all configuration parameters
const form = ref({
  dataset: 'demo-dk',
  startDate: '',
  endDate: '',
  apikey: 'sk-xxx',
  platform: 'alibaba',

  trajectoryNum: 10000,
  trajectoryLen: 200,
  miniSegmentLen: 20,
  missingRatio: 0.2,
  minTimeInterval: 10,
  maxTimeInterval: 1e9,
  concurrentNum: 16,
  maxRetries: 3,

  miningModel:'qwen-flash',
  codingModel:'qwen-flash',
  retryTimes:3,
  eF:3e-3,

  imputationModel: 'qwen-flash',
  topK: 5,
})

// Computed property to check if custom dataset is selected
const isCustomDataset = computed(() => {
  return form.value.dataset.includes('custom')
})

// Computed property for date range validation based on dataset selection
const dateRange = computed(() => {
  if (form.value.dataset === 'custom-dk') {
    return {
      min: '2024-03-01',
      max: '2024-03-31'
    }
  } else if (form.value.dataset === 'custom-us') {
    return {
      min: '2024-04-01',
      max: '2024-04-30'
    }
  }
  return {
    min: '',
    max: ''
  }
})

// Computed property for date range hint text
const dateRangeHint = computed(() => {
  if (form.value.dataset === 'custom-dk') {
    return 'DK dataset only supports data from March 2024.'
  } else if (form.value.dataset === 'custom-us') {
    return 'US dataset only supports data from April 2024.'
  }
  return 'Define the time range for your custom dataset.'
})

// SD-KG construction status and progress
const sdkgStatus = ref('idle')
const sdkgProgress = ref(0)
let sdkgTimer = null

// Imputation status and progress
const imputeStatus = ref('idle')
const imputeProgress = ref(0)
let imputeTimer = null

// CLEAR content update status and progress
const updateStatus = ref('idle')
const updateProgress = ref(0)
let updateTimer = null

/**
 * Start SD-KG construction process
 * Sends configuration to backend and initiates progress polling
 */
const startSdkgBuild = async () => {
  sdkgStatus.value = 'running'
  sdkgProgress.value = 0

  const requestData = {
    startDate: form.value.startDate,
    endDate: form.value.endDate,

    dataset: form.value.dataset,
    apikey: form.value.apikey,
    platform: form.value.platform,
    miningModel: form.value.miningModel,
    codingModel: form.value.codingModel,
    imputationModel: form.value.imputationModel,

    topK: form.value.topK,
    trajectoryNum: form.value.trajectoryNum,
    trajectoryLen: form.value.trajectoryLen,
    miniSegmentLen: form.value.miniSegmentLen,
    missingRatio: form.value.missingRatio,
    minTimeInterval: form.value.minTimeInterval,
    maxTimeInterval: form.value.maxTimeInterval,
    eF: form.value.eF,
    concurrentNum: form.value.concurrentNum,
    maxRetries: form.value.maxRetries,
    retryTimes: form.value.retryTimes,
  }

  const res = await fetch('http://localhost:8000/api/v1/vista/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  })

  const data = await res.json()
  sdkgTaskId.value = data.task_id

  pollSdkgProgress()
}

/**
 * Poll SD-KG construction progress from backend
 * Updates progress bar and status based on backend response
 */
const pollSdkgProgress = () => {
  if (sdkgTimer) clearInterval(sdkgTimer)

  sdkgTimer = setInterval(async () => {
    const res = await fetch(`http://localhost:8000/api/v1/vista/task/${sdkgTaskId.value}`)
    const data = await res.json()

    sdkgProgress.value = data.progress

    if (data.status === 'done') {
      sdkgStatus.value = 'done'
      clearInterval(sdkgTimer)
    }
  }, 1000)
}

/**
 * Start trajectory imputation process
 * Only runs if SD-KG construction is completed
 */
const startImputation = async () => {
  if (sdkgStatus.value !== 'done') return

  imputeStatus.value = 'running'
  imputeProgress.value = 0

  const requestData = {
    startDate: form.value.startDate,
    endDate: form.value.endDate,
    dataset: form.value.dataset,
    apikey: form.value.apikey,
    platform: form.value.platform,
    imputationModel: form.value.imputationModel,

    topK: form.value.topK,
    trajectoryNum: form.value.trajectoryNum,
    trajectoryLen: form.value.trajectoryLen,
    miniSegmentLen: form.value.miniSegmentLen,
    missingRatio: form.value.missingRatio,
    minTimeInterval: form.value.minTimeInterval,
    maxTimeInterval: form.value.maxTimeInterval,
    eF: form.value.eF,
    concurrentNum: form.value.concurrentNum,
    maxRetries: form.value.maxRetries,
    retryTimes: form.value.retryTimes,
  }

  const res = await fetch('http://localhost:8000/api/v1/vista/impute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  })

  const data = await res.json()
  imputeTaskId.value = data.task_id

  pollImputeProgress()
}

/**
 * Poll imputation progress from backend
 * Updates progress bar and status based on backend response
 */
const pollImputeProgress = () => {
  if (imputeTimer) clearInterval(imputeTimer)

  imputeTimer = setInterval(async () => {
    const res = await fetch(`http://localhost:8000/api/v1/vista/task/${imputeTaskId.value}`)
    const data = await res.json()

    imputeProgress.value = data.progress

    if (data.status === 'done') {
      imputeStatus.value = 'done'
      clearInterval(imputeTimer)
    }
  }, 1000)
}

/**
 * Update CLEAR content with SD-KG and imputation results
 * Only runs if both SD-KG construction and imputation are completed
 */
const updateCLEARContent = async () => {
  if (sdkgStatus.value !== 'done' || imputeStatus.value !== 'done') return

  updateStatus.value = 'running'
  updateProgress.value = 0

  const requestData = {
    minTimeInterval: form.value.minTimeInterval,
    maxTimeInterval: form.value.maxTimeInterval,
    startDate: form.value.startDate,
    endDate: form.value.endDate,
    dataset: form.value.dataset,
    sdkgTaskId: sdkgTaskId.value,
    imputeTaskId: imputeTaskId.value,
    apikey: form.value.apikey,
    platform: form.value.platform,
    trajectoryNum: form.value.trajectoryNum,
    trajectoryLen: form.value.trajectoryLen,
  }

  try {
    const res = await fetch('http://localhost:8000/api/v1/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    })

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }

    const data = await res.json()
    updateTaskId.value = data.task_id

    pollUpdateProgress()
  } catch (error) {
    console.error('Failed to update CLEAR content:', error)
    updateStatus.value = 'error'
    updateProgress.value = 0
  }
}

/**
 * Poll CLEAR content update progress from backend
 * Updates progress bar and status based on backend response
 */
const pollUpdateProgress = () => {
  if (updateTimer) clearInterval(updateTimer)

  updateTimer = setInterval(async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/update/task/${updateTaskId.value}`)
      const data = await res.json()

      updateProgress.value = data.progress
      updateStatus.value = data.status 

      if (data.status === 'done' || data.status === 'error' || data.status === 'cancelled') {
        clearInterval(updateTimer)
      }
    } catch (error) {
      console.error('Failed to poll update progress:', error)
      clearInterval(updateTimer)
      updateStatus.value = 'error'
    }
  }, 1000)
}

// Cleanup timers on component unmount
onBeforeUnmount(() => {
  if (sdkgTimer) window.clearInterval(sdkgTimer)
  if (imputeTimer) window.clearInterval(imputeTimer)
  if (updateTimer) window.clearInterval(updateTimer)
})
</script>

<style scoped>
/* Main panel container with improved visual hierarchy */
.panel {
  width: 100%;
  flex: 1;
  min-height: 0; 
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e2e8f0, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Enhanced panel header with gradient background and decorative elements */
.panel-header {
  padding: 2.5rem 2rem 1.5rem 2rem;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid #e2e8f0;
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

/* Title container with improved typography and spacing */
.title-container {
  position: relative;
  z-index: 2;

}

/* Main title with consistent font size and gradient effect */
.title {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.2;
  color: #1e293b;
}

/* Gradient text effect matching other pages */
.gradient-text {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* Subtitle with improved readability */
.subtitle {
  margin: 0;
  font-size: 1.125rem;
  line-height: 1.6;
  color: #475569;
  max-width: 800px;
}

.panel-body {
  flex: 1;
  min-height: 0; 
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 1.5rem;
  padding: 1.5rem 2rem 2rem 2rem;
  box-sizing: border-box;
}

.left,
.right {
  min-height: 0;
  height: 100%;
  overflow: auto;
}

/* Section styling with improved visual design */
.section {
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #1e293b;
}

.section-hint {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #64748b;
  margin: 0 0 1rem 0;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.field-label {
  flex: 0 0 180px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.field-input {
  flex: 1;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  transition: all 0.2s ease;
}

.field-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Expert groups with improved visual hierarchy */
.expert-group {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.expert-group-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e2e8f0;
}

/* Pipeline section with enhanced visual design */
.pipeline-section {
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  height: 100%;
  box-sizing: border-box;
  max-height: 600px;
  overflow-y: auto;
}

.pipeline-card {
  margin-top: 1rem;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  transition: all 0.2s ease;
}

.pipeline-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.pipeline-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.pipeline-text {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #64748b;
  margin: 0;
}

/* Action button with modern gradient effect */
.action-btn {
  align-self: flex-start;
  border-radius: 8px;
  border: none;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 120px;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.action-btn:disabled {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Progress bar styling */
.progress-row {
  margin-top: 1rem;
}

.progress {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #f1f5f9;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
  transition: width 0.3s ease;
}

.progress-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #64748b;
}

/* Custom dataset card with visual emphasis */
.custom-dataset-card {
  margin-top: 1rem;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-left: 4px solid #3b82f6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.custom-dataset-header {
  margin-bottom: 1rem;
}

.custom-dataset-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.custom-dataset-text {
  font-size: 0.75rem;
  line-height: 1.5;
  color: #64748b;
  margin: 0;
}

/* Responsive design adjustments */
@media (max-width: 1024px) {
  .panel-header {
    padding: 2rem 1.5rem 1.25rem 1.5rem;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .panel-body {
    grid-template-columns: 1fr;
    gap: 1.25rem;
    padding: 1.25rem 1.5rem 1.5rem 1.5rem;
  }
  
  .pipeline-section {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .panel-header {
    padding: 1.5rem 1rem 1rem 1rem;
  }
  
  .title {
    font-size: 1.75rem;
  }
  
  .subtitle {
    font-size: 0.875rem;
  }
  
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
  
  .field-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .field-label {
    flex: none;
    width: 100%;
  }
  
  .field-input {
    width: 100%;
  }
  
  .pipeline-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .action-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .panel {
    border-radius: 12px;
  }
  
  .title {
    font-size: 1.5rem;
  }
  
  .subtitle {
    font-size: 0.75rem;
  }
  
  .section {
    padding: 1rem;
  }
  
  .expert-group {
    padding: 1rem;
  }
  
  .pipeline-card {
    padding: 1rem;
  }
}
</style>