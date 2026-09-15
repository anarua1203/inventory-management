import { ref, computed } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

// Shared sidebar state (singleton pattern, same approach as useFilters/useAuth)
const collapsed = ref(getInitialCollapsed())
const mobileOpen = ref(false)

// Element that opened the mobile drawer, so we can return focus to it on close
let mobileTriggerEl = null

function getInitialCollapsed() {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch (err) {
    // localStorage unavailable (e.g. private browsing) - default to expanded
    return false
  }
}

export function useSidebar() {
  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed.value))
    } catch (err) {
      // Ignore write failures
    }
  }

  // Opens the mobile drawer; triggerEl is the button that triggered it,
  // used to restore focus when the drawer closes
  const openMobile = (triggerEl) => {
    mobileTriggerEl = triggerEl || null
    mobileOpen.value = true
  }

  const closeMobile = () => {
    if (!mobileOpen.value) return
    mobileOpen.value = false
    if (mobileTriggerEl && typeof mobileTriggerEl.focus === 'function') {
      mobileTriggerEl.focus()
    }
  }

  // Effective width used to offset the main content area on desktop
  const sidebarWidth = computed(() => {
    return collapsed.value ? 'var(--sidebar-w-collapsed)' : 'var(--sidebar-w-expanded)'
  })

  return {
    collapsed,
    mobileOpen,
    toggleCollapsed,
    openMobile,
    closeMobile,
    sidebarWidth
  }
}
