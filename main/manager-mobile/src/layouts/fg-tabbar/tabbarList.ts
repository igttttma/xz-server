import type { TabBar } from '@uni-helper/vite-plugin-uni-pages'

type FgTabBarItem = TabBar['list'][0] & {
  icon: string
  iconType: 'uiLib' | 'unocss' | 'iconfont'
}

/**
 * Tabbar selection strategy; see tabbar.md for details
 * 0: 'NO_TABBAR' `no tabbar`
 * 1: 'NATIVE_TABBAR' `fully native tabbar`
 * 2: 'CUSTOM_TABBAR_WITH_CACHE' `custom tabbar with cache`
 * 3: 'CUSTOM_TABBAR_WITHOUT_CACHE' `custom tabbar without cache`
 *
 * Note: after changing any code in this file, rerun the app; otherwise pages.json will not update and errors may occur
 */
export const TABBAR_MAP = {
  NO_TABBAR: 0,
  NATIVE_TABBAR: 1,
  CUSTOM_TABBAR_WITH_CACHE: 2,
  CUSTOM_TABBAR_WITHOUT_CACHE: 3,
}
// TODO: switch the tabbar strategy here
export const selectedTabbarStrategy = TABBAR_MAP.NATIVE_TABBAR

// When selectedTabbarStrategy==NATIVE_TABBAR(1), iconPath and selectedIconPath are required
// When selectedTabbarStrategy==CUSTOM_TABBAR(2,3), icon and iconType are required
// When selectedTabbarStrategy==NO_TABBAR(0), tabbarList has no effect
export const tabbarList: FgTabBarItem[] = [
  {
    iconPath: 'static/tabbar/robot.png',
    selectedIconPath: 'static/tabbar/robot_activate.png',
    pagePath: 'pages/index/index',
    text: 'Home',
    icon: 'home',
    // When using a built-in UI framework icon, iconType is uiLib
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/network.png',
    selectedIconPath: 'static/tabbar/network_activate.png',
    pagePath: 'pages/device-config/index',
    text: 'Network Config',
    icon: 'i-carbon-network-3',
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/system.png',
    selectedIconPath: 'static/tabbar/system_activate.png',
    pagePath: 'pages/settings/index',
    text: 'System',
    icon: 'i-carbon-settings',
    iconType: 'uiLib',
  },
]

// NATIVE_TABBAR(1) and CUSTOM_TABBAR_WITH_CACHE(2) require the tabbar cache
export const cacheTabbarEnable = selectedTabbarStrategy === TABBAR_MAP.NATIVE_TABBAR
  || selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE

const _tabbar: TabBar = {
  // Only the WeChat Mini Program supports custom; it has no effect on App and H5
  custom: selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE,
  color: '#e6e6e6',
  selectedColor: '#667dea',
  backgroundColor: '#fff',
  borderStyle: 'black',
  height: '50px',
  fontSize: '10px',
  iconWidth: '24px',
  spacing: '3px',
  list: tabbarList as unknown as TabBar['list'],
}

// 0 and 1 need the various bottom tabbar settings to leverage the cache
export const tabBar = cacheTabbarEnable ? _tabbar : undefined
