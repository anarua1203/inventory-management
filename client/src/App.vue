<template>
  <div class="app">
    <a href="#main-content" class="skip-link">{{ t('nav.skipToContent') }}</a>

    <AppSidebar
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />

    <div class="app-main" :class="{ 'sidebar-collapsed': collapsed }">
      <header class="mobile-header">
        <button
          type="button"
          class="mobile-menu-btn"
          :aria-label="mobileOpen ? t('nav.closeMenu') : t('nav.openMenu')"
          aria-controls="app-sidebar"
          :aria-expanded="mobileOpen"
          @click="mobileOpen ? closeMobile() : openMobile($event.currentTarget)"
        >
          <NavIcon :name="mobileOpen ? 'close' : 'menu'" />
        </button>
        <span class="mobile-header-title">{{ t('nav.companyName') }}</span>
      </header>

      <FilterBar />

      <main id="main-content" class="main-content" tabindex="-1">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useSidebar } from './composables/useSidebar'
import AppSidebar from './components/AppSidebar.vue'
import NavIcon from './components/NavIcon.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    NavIcon,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { collapsed, mobileOpen, openMobile, closeMobile } = useSidebar()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      collapsed,
      mobileOpen,
      openMobile,
      closeMobile,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  /* Spacing (4px scale) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 10px 25px rgba(15, 23, 42, 0.12);

  /* Colors */
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f5f9;
  --color-accent: #2563eb;
  --color-accent-soft: #eff6ff;
  --color-accent-text: #1d4ed8;

  /* Layout */
  --sidebar-w-expanded: 240px;
  --sidebar-w-collapsed: 64px;
  --mobile-header-h: 56px;
  --content-max: 1440px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: var(--space-4);
  background: var(--color-accent);
  color: #ffffff;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  z-index: 1000;
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: var(--space-4);
}

.app-main {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  margin-left: 0;
  transition: margin-left 0.2s ease;
}

@media (min-width: 1024px) {
  .app-main {
    margin-left: var(--sidebar-w-expanded);
  }
  .app-main.sidebar-collapsed {
    margin-left: var(--sidebar-w-collapsed);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-main {
    transition: none;
  }
}

.mobile-header {
  display: none;
}

@media (max-width: 1023.98px) {
  .mobile-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: var(--mobile-header-h);
    padding: 0 var(--space-4);
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 150;
  }
}

.mobile-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.mobile-menu-btn:hover {
  background: var(--color-surface-hover);
}

.mobile-header-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-8);
}

.main-content:focus {
  outline: none;
}

@media (max-width: 767.98px) {
  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.9375rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: #2563eb;
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.loading {
  text-align: center;
  padding: var(--space-10) var(--space-6);
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
</style>
