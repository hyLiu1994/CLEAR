<template>
  <AppPageLayout>
    <section class="panel">
      <!-- Top title area -->
      <header class="panel-header">
        <div>
          <h1 class="title">CLEAR: A Knowledge-Centric Vessel Trajectory Platform</h1>
          <p class="subtitle">
            CLEAR constructs a Structured Data-derived Knowledge Graph (SD-KG) from AIS records
            and uses it to impute missing trajectory segments and support interactive vessel analysis.
          </p>
          <p class="subtitle secondary">
            The <strong>Map</strong> view exposes enriched trajectories on a marine basemap, the
            <strong>SD-KG</strong> view reveals the knowledge that drives imputations, and
            <strong>Settings</strong> lets you choose datasets, processing pipelines, and
            hyperparameters. Together they form a coherent, knowledge-centric analytics platform.
          </p>
        </div>
      </header>

      <!-- Main entry area -->
      <div class="panel-body">
        <div class="entry-grid">
          <!-- Map -->
          <button class="entry-card" @click="go('/map')">
            <div class="entry-chip">Map</div>
            <h2 class="entry-title">Trajectory Map View</h2>
            <p class="entry-text">
              Visualize raw and imputed vessel trajectories on an interactive maritime map.
              Zoom into individual segments, inspect gaps, and compare reconstructed tracks
              with their original observations.
            </p>
            <p class="entry-footer-link">View Map →</p>
          </button>

          <!-- SD-KG -->
          <button class="entry-card" @click="go('/sdkg')">
            <div class="entry-chip">SD-KG</div>
            <h2 class="entry-title">Knowledge Graph Viewer</h2>
            <p class="entry-text">
              Explore the Structured Data-derived Knowledge Graph that links static attributes,
              behavior patterns, and imputation functions. Inspect how frequently patterns occur
              and how they support specific reconstruction choices.
            </p>
            <p class="entry-footer-link">Browse SD-KG →</p>
          </button>

          <!-- Settings / Personalization -->
          <button class="entry-card" @click="go('/settings')">
            <div class="entry-chip">Settings</div>
            <h2 class="entry-title">Personalized Configuration</h2>
            <p class="entry-text">
              Select example or custom AIS datasets, configure the processing pipeline, and
              tune imputation hyperparameters. Use these settings to tailor CLEAR to different
              scenarios or demonstration profiles.
            </p>
            <p class="entry-footer-link">Open Settings →</p>
          </button>
        </div>
      </div>
    </section>
  </AppPageLayout>
</template>

<script setup>
import { useRouter } from 'vue-router'
import AppPageLayout from '../components/AppPageLayout.vue'

const router = useRouter()

const go = (path) => {
  if (router.currentRoute.value.path !== path) {
    router.push(path)
  }
}
</script>

<style scoped>
/* Full-page panel: consistent with Settings / SD-KG style */
.panel {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 0 0 1px #e5e5e5, 0 20px 40px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

/* Top title area */
.panel-header {
  padding: 18px 22px 10px 22px;
  border-bottom: 1px solid #e5e7eb;
}

.title {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  max-width: 760px;
}

.subtitle.secondary {
  margin-top: 4px;
  color: #6b7280;
}

/* Main body */
.panel-body {
  flex: 1;
  padding: 16px 22px 20px 22px;
  box-sizing: border-box;
}

/* Three entry cards */
.entry-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.entry-card {
  text-align: left;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 16px 14px 12px 14px;
  cursor: pointer;
  outline: none;

  display: flex;
  flex-direction: column;
  justify-content: flex-start;

  transition:
    background 0.12s ease,
    box-shadow 0.12s ease,
    transform 0.12s ease,
    border-color 0.12s ease;
}

.entry-card:hover {
  background: #ffffff;
  border-color: #c4d2ff;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.14);
  transform: translateY(-1px);
}

.entry-chip {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.entry-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 6px 0;
}

.entry-text {
  margin: 0;
  font-size: 12px;
  color: #4b5563;
  flex: 1;
}

/* Bottom link style */
.entry-footer-link {
  margin: 10px 0 0 0;
  font-size: 12px;
  font-weight: 500;
  color: #2563eb;
}

/* Responsive */
@media (max-width: 900px) {
  .entry-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .panel-header {
    padding: 14px 14px 8px 14px;
  }

  .panel-body {
    padding: 12px 14px 14px 14px;
  }

  .entry-grid {
    grid-template-columns: 1fr;
  }
}
</style>
