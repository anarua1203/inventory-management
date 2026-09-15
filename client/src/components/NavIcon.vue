<template>
  <svg
    class="nav-icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'overview'">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </template>
    <template v-else-if="name === 'inventory'">
      <path d="M3 7l9-4 9 4-9 4-9-4z" />
      <path d="M3 7v10l9 4 9-4V7" />
      <path d="M12 11v10" />
    </template>
    <template v-else-if="name === 'orders'">
      <path d="M6 3h9l3 4v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M9 8h6" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </template>
    <template v-else-if="name === 'finance'">
      <path d="M3 12l4-4 4 3 6-7 4 4" />
      <path d="M3 20h18" />
    </template>
    <template v-else-if="name === 'demand'">
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <rect x="7" y="12" width="3" height="7" />
      <rect x="12" y="8" width="3" height="11" />
      <rect x="17" y="4" width="3" height="15" />
    </template>
    <template v-else-if="name === 'restocking'">
      <path d="M21 8V5a1 1 0 0 0-1-1h-3" />
      <path d="M3 8V5a1 1 0 0 1 1-1h3" />
      <path d="M21 16v3a1 1 0 0 1-1 1h-3" />
      <path d="M3 16v3a1 1 0 0 0 1 1h3" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </template>
    <template v-else-if="name === 'reports'">
      <rect x="4" y="4" width="16" height="16" rx="1.5" />
      <path d="M8 16v-4" />
      <path d="M12 16V8" />
      <path d="M16 16v-6" />
    </template>
    <template v-else-if="name === 'chevron-left'">
      <path d="M15 6l-6 6 6 6" />
    </template>
    <template v-else-if="name === 'chevron-right'">
      <path d="M9 6l6 6-6 6" />
    </template>
    <template v-else-if="name === 'menu'">
      <path d="M4 6h16" />
      <path d="M4 12h16" />
      <path d="M4 18h16" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </template>
  </svg>
</template>

<script>
export default {
  name: 'NavIcon',
  props: {
    name: {
      type: String,
      required: true
    }
  }
}
</script>

<style scoped>
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
</style>
