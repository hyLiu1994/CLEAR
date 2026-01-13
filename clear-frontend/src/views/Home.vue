<template>
  <AppPageLayout>
    <!-- Main container with modern gradient background -->
    <main class="home-container">
      <!-- Hero section with title and description -->
      <section class="hero-section">
        <div class="hero-content">
          <!-- Decorative element -->
          <div class="hero-decoration">
            <div class="decoration-circle"></div>
            <div class="decoration-circle"></div>
            <div class="decoration-circle"></div>
          </div>
          
          <!-- Main title with gradient -->
          <h1 class="hero-title">
            CLEAR: A Knowledge-Centric<br>
            <span class="gradient-text">Vessel Trajectory Platform</span>
          </h1>
          
          <!-- Description with improved readability -->
          <p class="hero-description">
            CLEAR constructs a <strong>Structured Data-derived Knowledge Graph (SD-KG)</strong> from AIS records 
            and uses it to impute missing trajectory segments while supporting interactive vessel analysis.
          </p>
        </div>
      </section>

      <!-- Feature cards section -->
      <div class="features-grid">
        <!-- Map feature card -->
        <article class="feature-card" @click="go('/map')" role="button" tabindex="0">
          <div class="card-header">
            <div class="card-badge card-badge-map">Map</div>
            <div class="card-icon">🌊</div>
          </div>
          <div class="card-content">
            <h3 class="card-title">Trajectory Map View</h3>
            <p class="card-description">
              Visualize raw and imputed vessel trajectories on an interactive maritime map. 
              Zoom into individual segments, inspect gaps, and compare reconstructed tracks 
              with original observations.
            </p>
          </div>
          <div class="card-footer">
            <span class="card-link">View Map</span>
            <svg class="arrow-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="card-hover-effect"></div>
        </article>

        <!-- SD-KG feature card -->
        <article class="feature-card" @click="go('/sdkg')" role="button" tabindex="0">
          <div class="card-header">
            <div class="card-badge card-badge-sdkg">SD-KG</div>
            <div class="card-icon">🕸️</div>
          </div>
          <div class="card-content">
            <h3 class="card-title">Knowledge Graph Viewer</h3>
            <p class="card-description">
              Explore the Structured Data-derived Knowledge Graph that links static attributes, 
              behavior patterns, and imputation functions. Inspect pattern frequencies and 
              reconstruction choices.
            </p>
          </div>
          <div class="card-footer">
            <span class="card-link">Browse SD-KG</span>
            <svg class="arrow-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="card-hover-effect"></div>
        </article>

        <!-- Settings feature card -->
        <article class="feature-card" @click="go('/settings')" role="button" tabindex="0">
          <div class="card-header">
            <div class="card-badge card-badge-settings">Settings</div>
            <div class="card-icon">⚙️</div>
          </div>
          <div class="card-content">
            <h3 class="card-title">Personalized Configuration</h3>
            <p class="card-description">
              Select example or custom AIS datasets, configure processing pipelines, and 
              tune imputation hyperparameters. Tailor CLEAR to different scenarios and 
              demonstration profiles.
            </p>
          </div>
          <div class="card-footer">
            <span class="card-link">Open Settings</span>
            <svg class="arrow-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="card-hover-effect"></div>
        </article>
      </div>
    </main>
  </AppPageLayout>
</template>

<script setup>
// Import Vue Router for navigation
import { useRouter } from 'vue-router'
import AppPageLayout from '../components/AppPageLayout.vue'

const router = useRouter()

// Navigation function with route validation
const go = (path) => {
  if (router.currentRoute.value.path !== path) {
    router.push(path)
  }
}
</script>

<style scoped>
/* Main container styles */
.home-container {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 0;
  margin: 0;
}

/* Hero section styles */
.hero-section {
  padding: 4rem 2rem 3rem;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid #e2e8f0;
  position: relative;
  overflow: hidden;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
  text-align: center;
}

.hero-decoration {
  position: absolute;
  top: -50px;
  right: -50px;
  z-index: 1;
}

.decoration-circle {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
  position: absolute;
  top: 0;
  right: 0;
}

.decoration-circle:nth-child(2) {
  width: 200px;
  height: 200px;
  top: 50px;
  right: 50px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%);
}

.decoration-circle:nth-child(3) {
  width: 100px;
  height: 100px;
  top: 100px;
  right: 100px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%);
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.2;
  color: #1e293b;
  margin-bottom: 1.5rem;
  position: relative;
}

.gradient-text {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 1.25rem;
  line-height: 1.6;
  color: #475569;
  max-width: 800px;
  margin: 0 auto;
}

.hero-description strong {
  color: #3b82f6;
  font-weight: 600;
}

/* Features grid - centered below hero */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(280px, 360px));
  gap: 2rem;
  max-width: 1200px;
  margin: 3rem auto;
  padding: 0 2rem;
}

/* Feature card styles */
.feature-card {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 320px;
  outline: none;
}

.feature-card:hover,
.feature-card:focus {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.feature-card:active {
  transform: translateY(-2px);
}

.card-hover-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.feature-card:hover .card-hover-effect {
  transform: scaleX(1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.card-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.card-badge-map {
  background: rgba(59, 130, 246, 0.1);
  color: #1d4ed8;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.card-badge-sdkg {
  background: rgba(139, 92, 246, 0.1);
  color: #7c3aed;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.card-badge-settings {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.card-icon {
  font-size: 1.75rem;
  opacity: 0.8;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1rem 0;
  line-height: 1.3;
}

.card-description {
  font-size: 0.95rem;
  line-height: 1.5;
  color: #475569;
  margin: 0;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid #f1f5f9;
}

.card-link {
  font-size: 0.95rem;
  font-weight: 600;
  color: #3b82f6;
  transition: color 0.2s ease;
}

.feature-card:hover .card-link {
  color: #2563eb;
}

.arrow-icon {
  width: 16px;
  height: 16px;
  color: #3b82f6;
  transition: transform 0.2s ease;
}

.feature-card:hover .arrow-icon {
  transform: translateX(4px);
}

/* Responsive design */
@media (max-width: 1024px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, minmax(280px, 1fr));
    max-width: 800px;
  }
  
  .hero-section {
    padding: 3rem 1.5rem 2rem;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-description {
    font-size: 1.125rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    max-width: 500px;
    gap: 1.5rem;
    margin: 2rem auto;
    padding: 0 1rem;
  }
  
  .hero-section {
    padding: 2.5rem 1rem 1.5rem;
  }
  
  .feature-card {
    min-height: 280px;
    padding: 1.75rem;
  }
  
  .card-title {
    font-size: 1.125rem;
  }
  
  .card-description {
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 1.75rem;
  }
  
  .hero-description {
    font-size: 1rem;
  }
  
  .features-grid {
    gap: 1.25rem;
  }
  
  .feature-card {
    padding: 1.5rem;
    min-height: 260px;
  }
}
</style>