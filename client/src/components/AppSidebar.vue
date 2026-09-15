<template>
  <div>
    <div
      v-if="mobileOpen"
      class="sidebar-backdrop"
      @click="closeMobile"
    ></div>

    <aside
      id="app-sidebar"
      class="app-sidebar"
      :class="{ collapsed: collapsed, 'mobile-open': mobileOpen }"
    >
      <div class="sidebar-brand">
        <router-link to="/" class="brand-link" :aria-label="t('nav.companyName')">
          <span class="brand-monogram" aria-hidden="true">{{ companyInitial }}</span>
          <span class="brand-text">
            <span class="brand-name">{{ t('nav.companyName') }}</span>
            <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
          </span>
        </router-link>
      </div>

      <nav class="sidebar-nav" aria-label="Primary navigation">
        <ul class="nav-list" ref="navListEl">
          <li v-for="item in navItems" :key="item.to">
            <router-link
              :to="item.to"
              class="nav-link"
              :title="t(item.labelKey)"
            >
              <NavIcon :name="item.icon" />
              <span class="nav-label">{{ t(item.labelKey) }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <div class="sidebar-footer">
        <div class="footer-controls">
          <LanguageSwitcher placement="top-start" :compact="collapsed" />
          <ProfileMenu
            placement="top-start"
            :compact="collapsed"
            @show-profile-details="$emit('show-profile-details')"
            @show-tasks="$emit('show-tasks')"
          />
        </div>

        <button
          type="button"
          class="collapse-toggle"
          :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :aria-expanded="!collapsed"
          aria-controls="app-sidebar"
          @click="toggleCollapsed"
        >
          <NavIcon :name="collapsed ? 'chevron-right' : 'chevron-left'" />
          <span class="nav-label">{{ collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar') }}</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script>
import { computed, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import NavIcon from './NavIcon.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

export default {
  name: 'AppSidebar',
  components: {
    NavIcon,
    LanguageSwitcher,
    ProfileMenu
  },
  emits: ['show-profile-details', 'show-tasks'],
  setup() {
    const { t } = useI18n()
    const route = useRoute()
    const { collapsed, mobileOpen, toggleCollapsed, closeMobile } = useSidebar()

    const navItems = [
      { to: '/', labelKey: 'nav.overview', icon: 'overview' },
      { to: '/inventory', labelKey: 'nav.inventory', icon: 'inventory' },
      { to: '/orders', labelKey: 'nav.orders', icon: 'orders' },
      { to: '/spending', labelKey: 'nav.finance', icon: 'finance' },
      { to: '/demand', labelKey: 'nav.demandForecast', icon: 'demand' },
      { to: '/restocking', labelKey: 'nav.restocking', icon: 'restocking' },
      { to: '/reports', labelKey: 'nav.reports', icon: 'reports' }
    ]

    const companyInitial = computed(() => {
      const name = t('nav.companyName')
      return name ? name.charAt(0).toUpperCase() : 'C'
    })

    const navListEl = ref(null)

    // Move focus to the first nav link when the mobile drawer opens,
    // and lock body scroll while it's open
    watch(mobileOpen, (isOpen) => {
      if (isOpen) {
        nextTick(() => {
          const firstLink = navListEl.value?.querySelector('a')
          if (firstLink) firstLink.focus()
        })
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = ''
      }
    })

    // Close the drawer whenever the route changes
    watch(
      () => route.fullPath,
      () => {
        if (mobileOpen.value) closeMobile()
      }
    )

    const handleKeydown = (event) => {
      if (event.key === 'Escape' && mobileOpen.value) {
        closeMobile()
      }
    }

    onMounted(() => document.addEventListener('keydown', handleKeydown))
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleKeydown)
      document.body.style.overflow = ''
    })

    return {
      t,
      collapsed,
      mobileOpen,
      toggleCollapsed,
      closeMobile,
      navItems,
      companyInitial,
      navListEl
    }
  }
}
</script>

<style scoped>
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  z-index: 190;
}
@media (min-width: 1024px) {
  .sidebar-backdrop {
    display: none;
  }
}

.app-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 200;
  transform: translateX(-100%);
  transition: transform 0.2s ease;
}
.app-sidebar.mobile-open {
  transform: translateX(0);
}

@media (min-width: 1024px) {
  .app-sidebar {
    width: var(--sidebar-w-expanded);
    transform: none;
    transition: width 0.2s ease;
  }
  .app-sidebar.collapsed {
    width: var(--sidebar-w-collapsed);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-sidebar {
    transition: none;
  }
}

.sidebar-brand {
  flex-shrink: 0;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.brand-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
  min-height: 40px;
}

.brand-monogram {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  background: #0f172a;
  color: #ffffff;
  font-weight: 700;
  font-size: 0.9375rem;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (min-width: 1024px) {
  .app-sidebar.collapsed .brand-monogram {
    display: flex;
  }
  .app-sidebar.collapsed .brand-text {
    display: none;
  }
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3);
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.nav-link:not(.router-link-exact-active):hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.nav-link.router-link-exact-active {
  background: var(--color-accent-soft);
  color: var(--color-accent-text);
  font-weight: 600;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Visually hide labels in collapsed rail (desktop only) without removing
   them from the accessibility tree or the mobile drawer layout */
@media (min-width: 1024px) {
  .app-sidebar.collapsed .nav-label {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
  .app-sidebar.collapsed .nav-link {
    justify-content: center;
    padding: 0;
  }
}

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.footer-controls {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.collapse-toggle {
  display: none;
}

@media (min-width: 1024px) {
  .collapse-toggle {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-height: 40px;
    padding: 0 var(--space-3);
    border-radius: var(--radius-sm);
    border: none;
    background: none;
    color: var(--color-text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    font-family: inherit;
    cursor: pointer;
  }
  .collapse-toggle:hover {
    background: var(--color-surface-hover);
    color: var(--color-text);
  }
  .app-sidebar.collapsed .collapse-toggle {
    justify-content: center;
    padding: 0;
  }
}
</style>
