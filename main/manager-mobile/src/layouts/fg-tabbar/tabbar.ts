/**
 * Tabbar state; storageSync ensures the correct tabbar page after a browser refresh
 * Uses a simple reactive state instead of global pinia state
 */
export const tabbarStore = reactive({
  curIdx: uni.getStorageSync('app-tabbar-index') || 0,
  setCurIdx(idx: number) {
    this.curIdx = idx
    uni.setStorageSync('app-tabbar-index', idx)
  },
})
