<template>
  <AppPageLayout>
    <section class="panel">
      <!-- Top Title -->
      <header class="panel-header">
        <h1 class="title">Settings & Pipeline Control</h1>
        <p class="subtitle">
          Configure CLEAR's behavior for SD-KG construction and trajectory imputation.
        </p>
      </header>

      <div class="panel-body">
        <!-- Left: Mode + Hyperparameters -->
        <div class="left">
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

          <!-- Expert Mode -->
          <section class="section">
            <h2 class="section-title">VISTA configuration</h2>
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
              <div class="field-row">
                <label class="field-label">Missing Ratio</label>
                <input
                  v-model.number="form.missingRatio"
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

        <!-- Right: Pipeline Control + Progress Bar -->
        <div class="right">
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
            <p class="small-note">
              In the demo, progress is simulated in the frontend. In a full deployment,
              these buttons would trigger backend jobs and stream their status updates.
            </p>
          </section>
        </div>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { ref, onBeforeUnmount, computed } from 'vue'
import AppPageLayout from '../components/AppPageLayout.vue'

//new taskid to contact with the backend
const sdkgTaskId = ref(null)
const imputeTaskId = ref(null)
const updateTaskId = ref(null)

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

const isCustomDataset = computed(() => {
  return form.value.dataset.includes('custom')
})


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

// date range hint
const dateRangeHint = computed(() => {
  if (form.value.dataset === 'custom-dk') {
    return 'DK dataset only supports data from March 2024.'
  } else if (form.value.dataset === 'custom-us') {
    return 'US dataset only supports data from April 2024.'
  }
  return 'Define the time range for your custom dataset.'
})



const sdkgStatus = ref('idle')
const sdkgProgress = ref(0)
let sdkgTimer = null

const imputeStatus = ref('idle')
const imputeProgress = ref(0)
let imputeTimer = null

const updateStatus = ref('idle')
const updateProgress = ref(0)
let updateTimer = null

//SDKG
const startSdkgBuild = async () => {
  sdkgStatus.value = 'running'
  sdkgProgress.value = 0

  const requestData = {
    //
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

//SDKG progress polling
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

//Imputation
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

//imputation progress polling
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


// update CLEAR content
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
    console.error('fail to update the content of CLEAR:', error)
    updateStatus.value = 'error'
    updateProgress.value = 0
  }
}

// update progress polling
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
      console.error('fail to update:', error)
      clearInterval(updateTimer)
      updateStatus.value = 'error'
    }
  }, 1000)
}

onBeforeUnmount(() => {
  if (sdkgTimer) window.clearInterval(sdkgTimer)
  if (imputeTimer) window.clearInterval(imputeTimer)
  if (updateTimer) window.clearInterval(updateTimer)
})
</script>

<style scoped>
.panel {
  width: 100%;
  flex: 1;
  min-height: 0; 
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e5e5e5, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 18px 22px 10px 22px;
  border-bottom: 1px solid #e5e7eb;
}

.title {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  max-width: 780px;
}

.panel-body {
  flex: 1;
  min-height: 0; 
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 16px;
  padding: 14px 22px 18px 22px;
  box-sizing: border-box;
}

.left,
.right {
  min-height: 0;
  height: 100%;
  overflow: auto;
}

.section {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #111827;
}

.section-hint {
  font-size: 11px;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.field-label {
  flex: 0 0 190px;
  font-size: 12px;
  color: #374151;
}

.field-input {
  flex: 1;
  font-size: 12px;
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #ffffff;
}

/* Expert groups */
.expert-group {
  margin-top: -2px;  
  padding: 4px 4px;  
  border-radius: 6px; 
  border: 1px solid #e0e0e0;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);  
}

.expert-group-title {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  margin-bottom: -2px;  
  padding-bottom: 0px; 
  border-bottom: 1px solid #f0f0f0;
}

.pipeline-section {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  height: 100%;
  box-sizing: border-box;
}

.pipeline-card {
  margin-top: 8px;
  padding: 10px 11px;
  border-radius: 9px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.pipeline-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.pipeline-text {
  font-size: 11px;
  color: #6b7280;
  margin: 2px 0 0 0;
}

/* progress + button */
.action-btn {
  align-self: flex-start;
  border-radius: 999px;
  border: none;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  background: #2563eb;
  color: #ffffff;
  cursor: pointer;
}

.action-btn:disabled {
  background: #9ca3af;
  cursor: default;
}

.progress-row {
  margin-top: 8px;
}

.progress {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #f3f4f6;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  border-radius: 999px;
  background: #2563eb;
  transition: width 0.12s linear;
}

.progress-label {
  margin-top: 4px;
  font-size: 11px;
  color: #6b7280;
}

.small-note {
  margin-top: 10px;
  font-size: 10px;
  color: #9ca3af;
}

@media (max-width: 900px) {
  .panel-body {
    grid-template-columns: 1fr;
  }
}

.custom-dataset-card {
  margin-top: 8px;
  margin-bottom: 16px;
  padding: 10px 11px;
  border-radius: 9px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  border-left: 4px solid #2563eb;
}

.custom-dataset-header {
  margin-bottom: 8px;
}

.custom-dataset-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 2px;
}

.custom-dataset-text {
  font-size: 11px;
  color: #6b7280;
  margin: 0;
}
</style>