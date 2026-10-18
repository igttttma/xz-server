import smCrypto from 'sm-crypto'
import { pages, subPackages } from '@/pages.json'

import { isMpWeixin } from './platform'

/**
 * Storage key for the runtime server address override
 */
export const SERVER_BASE_URL_OVERRIDE_KEY = 'server_base_url_override'

/**
 * Set/clear/get the runtime server address override
 */
export function setServerBaseUrlOverride(url: string) {
  uni.setStorageSync(SERVER_BASE_URL_OVERRIDE_KEY, url)
}

export function clearServerBaseUrlOverride() {
  uni.removeStorageSync(SERVER_BASE_URL_OVERRIDE_KEY)
}

export function getServerBaseUrlOverride(): string | null {
  const value = uni.getStorageSync(SERVER_BASE_URL_OVERRIDE_KEY)
  return value || null
}

export function getLastPage() {
  // getCurrentPages() always has at least one element, so no extra check is needed
  // const lastPage = getCurrentPages().at(-1)
  // The previous approach fails at build time on older Android versions, so use the following one [it still fails even though src/interceptions/prototype.ts was added]
  const pages = getCurrentPages()
  return pages[pages.length - 1]
}

/**
 * Get the path and redirectPath of the current page route
 * path, e.g. '/pages/login/index'
 * redirectPath, e.g. '/pages/demo/base/route-interceptor'
 */
export function currRoute() {
  const lastPage = getLastPage()
  const currRoute = (lastPage as any).$page
  // console.log('lastPage.$page:', currRoute)
  // console.log('lastPage.$page.fullpath:', currRoute.fullPath)
  // console.log('lastPage.$page.options:', currRoute.options)
  // console.log('lastPage.options:', (lastPage as any).options)
  // After testing on multiple platforms, only fullPath is reliable; the others are not
  const { fullPath } = currRoute as { fullPath: string }
  // console.log(fullPath)
  // eg: /pages/login/index?redirect=%2Fpages%2Fdemo%2Fbase%2Froute-interceptor (Mini Program)
  // eg: /pages/login/index?redirect=%2Fpages%2Froute-interceptor%2Findex%3Fname%3Dfeige%26age%3D30(h5)
  return getUrlObj(fullPath)
}

function ensureDecodeURIComponent(url: string) {
  if (url.startsWith('%')) {
    return ensureDecodeURIComponent(decodeURIComponent(url))
  }
  return url
}
/**
 * Parse the url into path and query
 * For example, input url: /pages/login/index?redirect=%2Fpages%2Fdemo%2Fbase%2Froute-interceptor
 * Output: {path: /pages/login/index, query: {redirect: /pages/demo/base/route-interceptor}}
 */
export function getUrlObj(url: string) {
  const [path, queryStr] = url.split('?')
  // console.log(path, queryStr)

  if (!queryStr) {
    return {
      path,
      query: {},
    }
  }
  const query: Record<string, string> = {}
  queryStr.split('&').forEach((item) => {
    const [key, value] = item.split('=')
    // console.log(key, value)
    query[key] = ensureDecodeURIComponent(value) // decodeURIComponent is applied uniformly here for compatibility with H5 and WeChat
  })
  return { path, query }
}
/**
 * Get all pages that require login, including the main package and subpackages
 * Kept generic: a key can be passed as the filter, defaults to needLogin, used together with route-block
 * If no key is passed, all pages are returned; if a key is passed, pages are filtered by that key
 */
export function getAllPages(key = 'needLogin') {
  // Handle the main package
  const mainPages = pages
    .filter(page => !key || page[key])
    .map(page => ({
      ...page,
      path: `/${page.path}`,
    }))

  // Handle subpackages
  const subPages: any[] = []
  subPackages.forEach((subPageObj) => {
    // console.log(subPageObj)
    const { root } = subPageObj

    subPageObj.pages
      .filter(page => !key || page[key])
      .forEach((page: { path: string } & Record<string, any>) => {
        subPages.push({
          ...page,
          path: `/${root}/${page.path}`,
        })
      })
  })
  const result = [...mainPages, ...subPages]
  // console.log(`getAllPages by ${key} result: `, result)
  return result
}

/**
 * Get all pages that require login, including the main package and subpackages
 * Returns only an array of paths
 */
export const getNeedLoginPages = (): string[] => getAllPages('needLogin').map(page => page.path)

/**
 * Get all pages that require login, including the main package and subpackages
 * Returns only an array of paths
 */
export const needLoginPages: string[] = getAllPages('needLogin').map(page => page.path)

/**
 * Determine the baseUrl to use based on the current WeChat Mini Program environment
 */
export function getEnvBaseUrl() {
  // If a user-defined override address exists, return it first
  const override = getServerBaseUrlOverride()
  if (override)
    return override

  // Request base URL (from env by default)
  let baseUrl = import.meta.env.VITE_SERVER_BASEURL

  // # You may need to set different upload URLs for develop, trial and release in the WeChat Mini Program. See the code below.
  const VITE_SERVER_BASEURL__WEIXIN_DEVELOP = 'https://ukw0y1.laf.run'
  const VITE_SERVER_BASEURL__WEIXIN_TRIAL = 'https://ukw0y1.laf.run'
  const VITE_SERVER_BASEURL__WEIXIN_RELEASE = 'https://ukw0y1.laf.run'

  // Distinguish WeChat Mini Program environments
  if (isMpWeixin) {
    const {
      miniProgram: { envVersion },
    } = uni.getAccountInfoSync()

    switch (envVersion) {
      case 'develop':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_DEVELOP || baseUrl
        break
      case 'trial':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_TRIAL || baseUrl
        break
      case 'release':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_RELEASE || baseUrl
        break
    }
  }

  return baseUrl
}

/**
 * Determine the UPLOAD_BASEURL to use based on the current WeChat Mini Program environment
 */
export function getEnvBaseUploadUrl() {
  // Request base URL
  let baseUploadUrl = import.meta.env.VITE_UPLOAD_BASEURL

  const VITE_UPLOAD_BASEURL__WEIXIN_DEVELOP = 'https://ukw0y1.laf.run/upload'
  const VITE_UPLOAD_BASEURL__WEIXIN_TRIAL = 'https://ukw0y1.laf.run/upload'
  const VITE_UPLOAD_BASEURL__WEIXIN_RELEASE = 'https://ukw0y1.laf.run/upload'

  // Distinguish WeChat Mini Program environments
  if (isMpWeixin) {
    const {
      miniProgram: { envVersion },
    } = uni.getAccountInfoSync()

    switch (envVersion) {
      case 'develop':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_DEVELOP || baseUploadUrl
        break
      case 'trial':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_TRIAL || baseUploadUrl
        break
      case 'release':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_RELEASE || baseUploadUrl
        break
    }
  }

  return baseUploadUrl
}

/**
 * Generate an SM2 key pair (hex format)
 * @returns {object} Object containing the public and private keys
 */
export function generateSm2KeyPairHex() {
  // Generate the SM2 key pair with the sm-crypto library
  const sm2 = smCrypto.sm2
  const keypair = sm2.generateKeyPairHex()

  return {
    publicKey: keypair.publicKey,
    privateKey: keypair.privateKey,
    clientPublicKey: keypair.publicKey, // Client public key
    clientPrivateKey: keypair.privateKey, // Client private key
  }
}

/**
 * SM2 public-key encryption
 * @param {string} publicKey Public key (hex format)
 * @param {string} plainText Plain text
 * @returns {string} Encrypted ciphertext (hex format)
 */
export function sm2Encrypt(publicKey: string, plainText: string): string {
  if (!publicKey) {
    throw new Error('Public key cannot be null or undefined')
  }

  if (!plainText) {
    throw new Error('Plain text cannot be empty')
  }

  const sm2 = smCrypto.sm2
  // SM2 encryption; add the 04 prefix to mark an uncompressed public key
  const encrypted = sm2.doEncrypt(plainText, publicKey, 1)
  // Convert to hex format (keep consistent with the backend and add the 04 prefix)
  const result = `04${encrypted}`

  return result
}

/**
 * SM2 private-key decryption
 * @param {string} privateKey Private key (hex format)
 * @param {string} cipherText Ciphertext (hex format)
 * @returns {string} Decrypted plain text
 */
export function sm2Decrypt(privateKey: string, cipherText: string): string {
  const sm2 = smCrypto.sm2
  // Remove the 04 prefix (keep consistent with the backend)
  const dataWithoutPrefix = cipherText.startsWith('04') ? cipherText.substring(2) : cipherText
  // SM2 decryption
  return sm2.doDecrypt(dataWithoutPrefix, privateKey, 1)
}

type AnyFunction = (...args: any[]) => any

interface DebouncedFunction extends AnyFunction {
  cancel: () => void
}

/**
 * Debounce function
 * @param fn Function to debounce
 * @param delay Delay in milliseconds, defaults to 500ms
 * @param immediate Whether to invoke immediately, defaults to false
 * @returns Debounced function
 */
export function debounce<T extends AnyFunction>(
  fn: T,
  delay = 500,
  immediate = false,
): DebouncedFunction {
  let timer: ReturnType<typeof setTimeout> | null = null

  const debounced = function (this: any, ...args: Parameters<T>) {
    if (timer) {
      clearTimeout(timer)
    }

    if (immediate && !timer) {
      fn.apply(this, args)
    }

    timer = setTimeout(() => {
      if (!immediate) {
        fn.apply(this, args)
      }
      timer = null
    }, delay)
  } as DebouncedFunction

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  return debounced
}

type DeepCloneTarget = string | number | boolean | null | undefined | object

/**
 * Deep clone method
 * @param target Target to clone
 * @returns The cloned object
 */
export function deepClone<T extends DeepCloneTarget>(target: T): T {
  if (target === null || typeof target !== 'object') {
    return target
  }

  if (target instanceof Date) {
    return new Date(target.getTime()) as any
  }

  if (Array.isArray(target)) {
    return target.map(item => deepClone(item)) as any
  }

  if (target instanceof Object) {
    const clonedObj = {} as T
    for (const key in target) {
      if (Object.prototype.hasOwnProperty.call(target, key)) {
        (clonedObj as any)[key] = deepClone((target as any)[key])
      }
    }
    return clonedObj
  }

  return target
}
