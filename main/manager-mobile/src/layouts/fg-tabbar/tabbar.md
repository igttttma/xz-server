# Tabbar Guide

`tabbar` has `4` variants:

- 0 `No tabbar`: only one page entry and no `tabbar` at the bottom; commonly used for temporary campaign pages.
- 1 `Native tabbar`: switch tabs with `switchTab`; `tabbar` pages are cached.
  - Pros: built-in native tabbar, rendered first, and cached.
  - Cons: only two image sets can be used for selected and unselected states; changing colors requires swapping images (or using iconfont).
- 2 `Cached custom tabbar`: switch tabs with `switchTab`; `tabbar` pages are cached. Uses a third-party UI library `tabbar` component and hides the native `tabbar`.
  - Pros: freely configure the desired `svg icon` and easily change font colors. Cached. Supports various fancy animations.
  - Cons: the tabbar flickers on the first tap.
- 3 `Uncached custom tabbar`: switch tabs with `navigateTo`; `tabbar` pages are not cached. Uses a third-party UI library `tabbar` component.
  - Pros: freely configure the desired svg icon and easily change font colors. Supports various fancy animations.
  - Cons: the `tabbar` flickers on the first tap, and nothing is cached.


> Note: fancy effects must be implemented yourself; this template does not provide them.
