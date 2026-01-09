<template>
  <AppPageLayout>
    <section class="panel">
      <!-- Top Title -->
      <header class="panel-header">
        <h1 class="title">Settings & Pipeline Control</h1>
        <p class="subtitle">
          Configure CLEAR's behavior for SD-KG construction and trajectory imputation.
          Choose a guided tutorial or an expert mode, then launch the pipeline stages below.
        </p>
      </header>

      <div class="panel-body">
        <!-- Left: Mode + Hyperparameters -->
        <div class="left">
          <!-- Mode Toggle -->
          <div class="mode-toggle">
            <div class="mode-label">Configuration mode</div>
            <div class="mode-buttons">
              <button
                class="mode-btn"
                :class="{ active: mode === 'tutorial' }"
                @click="setMode('tutorial')"
              >
                Tutorial · Step-by-step
              </button>
              <button
                class="mode-btn"
                :class="{ active: mode === 'expert' }"
                @click="setMode('expert')"
              >
                Expert · Direct parameters
              </button>
            </div>
          </div>

          <!-- Dataset Selection (Shared by Both Modes) -->
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
                <option value="custom">Custom · Uploaded dataset</option>
              </select>
            </div>
          </section>

          <!-- Tutorial Mode -->
          <section class="section" v-if="mode === 'tutorial'">
            <h2 class="section-title">Tutorial: Pipeline walkthrough</h2>
            <p class="section-hint">
              Follow the steps below to understand how CLEAR constructs the SD-KG and imputes missing segments.
            </p>
            <!-- Step 1 -->
            <div class="step-card">
              <div class="step-header">
                <div class="step-index">1</div>
                <div class="step-title">Select platform & API Key</div>
              </div>
              <p class="step-text">
                First, you need to select the platform you are using and enter the API KEY you obtained from the corresponding platform.
              </p>
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

            <!-- Step 2 -->
            <div class="step-card">
              <div class="step-header">
                <div class="step-index">2</div>
                <div class="step-title">Prepare segments & descriptors</div>
              </div>
              <p class="step-text">
                CLEAR first segments vessel tracks and extracts kinematic and spatial descriptors
                for each complete segment.
              </p>
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
              <div class="field-row">
                <label class="field-label">Trajectory number</label>
                <input
                  v-model.number="form.trajectoryNum"
                  type="number"
                  min="1"
                  class="field-input"
                />
              </div>
            </div>

            <!-- Step 3 -->
            <div class="step-card">
              <div class="step-header">
                <div class="step-index">3</div>
                <div class="step-title">Build SD-KG</div>
              </div>
              <p class="step-text">
                This step uses an LLM to extract behavior patterns and imputation functions from the data, then links them with static attributes to build the SD-KG.
              </p>
              <div class="field-row">
                <label class="field-label">Extract behavior model</label>
                <select v-model="form.miningModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
              <div class="field-row">
                <label class="field-label">Generate function model</label>
                <select v-model="form.codingModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
            </div>

            <!-- Step 4 -->
            <div class="step-card">
              <div class="step-header">
                <div class="step-index">4</div>
                <div class="step-title">Select imputation strategy</div>
              </div>
              <p class="step-text">
                For each gap, CLEAR chooses an imputation function based on SD-KG evidence and
                reconstructs the missing trajectory segment.
              </p>
              <div class="field-row">
                <label class="field-label">Imputation model</label>
                <select v-model="form.imputationModel" class="field-input">
                  <option value="qwen-plus">Qwen Plus</option>
                  <option value="qwen-turbo">Qwen Turbo</option>
                  <option value="qwen-max">Qwen Max</option>
                  <option value="qwen-flash">Qwen Flash</option>
                </select>
              </div>
            </div>
          </section>

          <!-- Expert Mode -->
          <section class="section" v-else>
            <h2 class="section-title">Expert configuration</h2>
            <p class="section-hint">
              Configure construction and imputation hyperparameters directly.
              Detailed explanations are omitted for a more compact view.
            </p>

            <div class="expert-group">
              <div class="expert-group-title">Dataset config</div>
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
import { ref, onBeforeUnmount } from 'vue'
import AppPageLayout from '../components/AppPageLayout.vue'

//新增taskid用来沟通后端////////////////////////////////////////////////////////////////////
const sdkgTaskId = ref(null)
const imputeTaskId = ref(null)
const updateTaskId = ref(null)

const mode = ref('tutorial')
const setMode = m => {
  mode.value = m
}

const form = ref({
  dataset: 'demo-dk',

  apikey: 'sk-9e7e3e34a14040cda60571ff6ed5d8fc',
  platform: 'alibaba',

  trajectoryNum: 10000,
  trajectoryLen: 200,
  miniSegmentLen: 20,
  missingRatio: 0.2,
  minTimeInterval: 60,
  maxTimeInterval: 1e9,
  concurrentNum: 5,
  maxRetries: 3,

  miningModel:'qwen-flash',
  codingModel:'qwen-flash',
  retryTimes:3,
  eF:3e-3,

  imputationModel: 'qwen-flash',
  topK: 5,
})

const sdkgStatus = ref('idle')
const sdkgProgress = ref(0)
let sdkgTimer = null

const imputeStatus = ref('idle')
const imputeProgress = ref(0)
let imputeTimer = null

// 在现有状态变量后面添加
const updateStatus = ref('idle')
const updateProgress = ref(0)
let updateTimer = null

//沟通SDKG构建后端
const startSdkgBuild = async () => {
  sdkgStatus.value = 'running'
  sdkgProgress.value = 0

  // 构建完整的参数对象
  const requestData = {
    // 前端form中的所有参数
    dataset: form.value.dataset,
    apikey: form.value.apikey,
    platform: form.value.platform,
    miningModel: form.value.miningModel,
    codingModel: form.value.codingModel,
    imputationModel: form.value.imputationModel,
    
    // 数值参数
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

//获得SDKG构建进度（不需要修改）
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

//沟通后端填补逻辑
const startImputation = async () => {
  if (sdkgStatus.value !== 'done') return

  imputeStatus.value = 'running'
  imputeProgress.value = 0

  // 构建完整的参数对象
  const requestData = {
    // 填补需要的参数
    dataset: form.value.dataset,
    apikey: form.value.apikey,
    platform: form.value.platform,
    imputationModel: form.value.imputationModel,
    
    // 数值参数
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
    
    // 可以添加SDKG构建阶段的一些结果参数
    // sdkgCheckpoint: sdkgTaskId.value // 如果需要关联之前的构建结果
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

//获取填补进度（不需要修改）
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


// 在现有方法后面添加updateCLEARContent方法
const updateCLEARContent = async () => {
  if (sdkgStatus.value !== 'done' || imputeStatus.value !== 'done') return

  updateStatus.value = 'running'
  updateProgress.value = 0

  // 构建请求数据
  const requestData = {
    dataset: form.value.dataset,
    // 可以传递之前任务的ID用于关联
    sdkgTaskId: sdkgTaskId.value,
    imputeTaskId: imputeTaskId.value,
    // 其他必要参数
    apikey: form.value.apikey,
    platform: form.value.platform,
    trajectoryNum: form.value.trajectoryNum,
    trajectoryLen: form.value.trajectoryLen,
  }

  try {
    // 调用后端的update接口（需要你后端先实现这个接口）
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

    // 开始轮询进度
    pollUpdateProgress()
  } catch (error) {
    console.error('更新CLEAR内容失败:', error)
    updateStatus.value = 'error'
    updateProgress.value = 0
  }
}

// 轮询更新进度
// 轮询更新进度 - 修复版本
const pollUpdateProgress = () => {
  if (updateTimer) clearInterval(updateTimer)

  updateTimer = setInterval(async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/update/task/${updateTaskId.value}`)
      const data = await res.json()

      updateProgress.value = data.progress
      updateStatus.value = data.status // 更新状态

      if (data.status === 'done' || data.status === 'error' || data.status === 'cancelled') {
        clearInterval(updateTimer)
        
        // 确保最终状态正确
        if (data.status === 'done') {
          updateStatus.value = 'done'
          updateProgress.value = 100
        }
      }
    } catch (error) {
      console.error('轮询更新进度失败:', error)
      clearInterval(updateTimer)
      // 可以添加错误状态处理
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

.mode-toggle {
  margin-bottom: 12px;
}

.mode-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
}

.mode-buttons {
  display: inline-flex;
  padding: 2px;
  border-radius: 999px;
  background: #f3f4f6;
}

.mode-btn {
  border: none;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
  background: transparent;
  color: #4b5563;
}

.mode-btn.active {
  background: #ffffff;
  box-shadow: 0 0 0 1px #d1d5db;
  color: #111827;
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

.step-card {
  margin-top: 8px;
  padding: 10px 11px;
  border-radius: 9px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.step-index {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #2563eb;
  color: #ffffff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-title {
  font-size: 12px;
  font-weight: 600;
  color: #111827;
}

.step-text {
  font-size: 11px;
  color: #6b7280;
  margin: 2px 0 6px 0;
}

/* Expert groups */
.expert-group {
  margin-top: -2px;  /* 减少上边距 */
  padding: 4px 4px;  /* 减少内边距 */
  border-radius: 6px;  /* 减小圆角 */
  border: 1px solid #e0e0e0;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);  /* 减小阴影 */
}

.expert-group-title {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  margin-bottom: -2px;  /* 减少下边距 */
  padding-bottom: 0px;  /* 减少内边距 */
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
</style>
