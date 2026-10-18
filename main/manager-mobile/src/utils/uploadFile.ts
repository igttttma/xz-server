import { getEnvBaseUrl } from './index'
import { toast } from './toast'

/**
 * Example usage of the file upload hook
 * @example
 * const { loading, error, data, progress, run } = useUpload<IUploadResult>(
 *   uploadUrl,
 *   {},
 *   {
 *     maxSize: 5, // Maximum 5 MB
 *     sourceType: ['album'], // Only allow selecting from the album
 *     onProgress: (p) => console.log(`Upload progress: ${p}%`),
 *     onSuccess: (res) => console.log('Upload succeeded', res),
 *     onError: (err) => console.error('Upload failed', err),
 *   },
 * )
 */

/**
 * URL configuration for file uploads
 */
export const uploadFileUrl = {
  /** User avatar upload endpoint (dynamically reads the active BaseURL) */
  get USER_AVATAR() {
    return `${getEnvBaseUrl()}/user/avatar`
  },
}

/**
 * Generic file upload function (accepts a file path directly)
 * @param url Upload URL
 * @param filePath Local file path
 * @param formData Additional form data
 * @param options Upload options
 */
export function useFileUpload<T = string>(url: string, filePath: string, formData: Record<string, any> = {}, options: Omit<UploadOptions, 'sourceType' | 'sizeType' | 'count'> = {}) {
  return useUpload<T>(
    url,
    formData,
    {
      ...options,
      sourceType: ['album'],
      sizeType: ['original'],
    },
    filePath,
  )
}

export interface UploadOptions {
  /** Maximum number of images that can be selected, defaults to 1 */
  count?: number
  /** Size of the selected images: original or compressed */
  sizeType?: Array<'original' | 'compressed'>
  /** Source of the selected images: album or camera */
  sourceType?: Array<'album' | 'camera'>
  /** File size limit, in MB */
  maxSize?: number //
  /** Upload progress callback */
  onProgress?: (progress: number) => void
  /** Upload success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Upload completion callback (regardless of success or failure) */
  onComplete?: () => void
}

/**
 * File upload hook
 * @template T Type of the data returned after a successful upload
 * @param url Upload URL
 * @param formData Additional form data
 * @param options Upload options
 * @returns Upload state and control object
 */
export function useUpload<T = string>(url: string, formData: Record<string, any> = {}, options: UploadOptions = {},
  /** Pass a file path directly, skipping the picker */
  directFilePath?: string) {
  /** Uploading state */
  const loading = ref(false)
  /** Upload error state */
  const error = ref(false)
  /** Response data after a successful upload */
  const data = ref<T>()
  /** Upload progress (0-100) */
  const progress = ref(0)

  /** Destructure upload options and apply defaults */
  const {
    /** Maximum number of images that can be selected */
    count = 1,
    /** Size of the selected images */
    sizeType = ['original', 'compressed'],
    /** Source of the selected images */
    sourceType = ['album', 'camera'],
    /** File size limit (MB) */
    maxSize = 10,
    /** Progress callback */
    onProgress,
    /** Success callback */
    onSuccess,
    /** Failure callback */
    onError,
    /** Completion callback */
    onComplete,
  } = options

  /**
   * Check whether the file size exceeds the limit
   * @param size File size (bytes)
   * @returns Whether the check passed
   */
  const checkFileSize = (size: number) => {
    const sizeInMB = size / 1024 / 1024
    if (sizeInMB > maxSize) {
      toast.warning(`File size cannot exceed ${maxSize}MB`)
      return false
    }
    return true
  }
  /**
   * Trigger file selection and upload
   * Uses a different picker depending on the platform:
   * - WeChat Mini Program uses chooseMedia
   * - Other platforms use chooseImage
   */
  const run = () => {
    if (directFilePath) {
      // Use the provided file path directly
      loading.value = true
      progress.value = 0
      uploadFile<T>({
        url,
        tempFilePath: directFilePath,
        formData,
        data,
        error,
        loading,
        progress,
        onProgress,
        onSuccess,
        onError,
        onComplete,
      })
      return
    }

    // #ifdef MP-WEIXIN
    // Use the chooseMedia API in the WeChat Mini Program environment
    uni.chooseMedia({
      count,
      mediaType: ['image'], // Images only
      sourceType,
      success: (res) => {
        const file = res.tempFiles[0]
        // Check whether the file size is within the limit
        if (!checkFileSize(file.size))
          return

        // Start uploading
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: file.tempFilePath,
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select media file:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif

    // #ifndef MP-WEIXIN
    // Use the chooseImage API on non-WeChat Mini Program platforms
    uni.chooseImage({
      count,
      sizeType,
      sourceType,
      success: (res) => {
        console.log('Image selected:', res)

        // Start uploading
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: res.tempFilePaths[0],
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select image:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif
  }

  return { loading, error, data, progress, run }
}

/**
 * File upload options interface
 * @template T Type of the data returned after a successful upload
 */
interface UploadFileOptions<T> {
  /** Upload URL */
  url: string
  /** Temporary file path */
  tempFilePath: string
  /** Additional form data */
  formData: Record<string, any>
  /** Response data after a successful upload */
  data: Ref<T | undefined>
  /** Upload error state */
  error: Ref<boolean>
  /** Uploading state */
  loading: Ref<boolean>
  /** Upload progress (0-100) */
  progress: Ref<number>
  /** Upload progress callback */
  onProgress?: (progress: number) => void
  /** Upload success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Upload completion callback */
  onComplete?: () => void
}

/**
 * Perform the file upload
 * @template T Type of the data returned after a successful upload
 * @param options Upload options
 */
function uploadFile<T>({
  url,
  tempFilePath,
  formData,
  data,
  error,
  loading,
  progress,
  onProgress,
  onSuccess,
  onError,
  onComplete,
}: UploadFileOptions<T>) {
  try {
    // Create the upload task
    const uploadTask = uni.uploadFile({
      url,
      filePath: tempFilePath,
      name: 'file', // Key corresponding to the file
      formData,
      header: {
        // No need to set Content-Type manually in the H5 environment; let the browser handle the multipart format
        // #ifndef H5
        'Content-Type': 'multipart/form-data',
        // #endif
      },
      // Ensure the file name is valid
      success: (uploadFileRes) => {
        console.log('File uploaded successfully:', uploadFileRes)
        try {
          // Parse the response data
          const { data: _data } = JSON.parse(uploadFileRes.data)
          // Upload succeeded
          data.value = _data as T
          onSuccess?.(_data)
        }
        catch (err) {
          // Response parsing error
          console.error('Failed to parse upload response:', err)
          error.value = true
          onError?.(new Error('Failed to parse upload response'))
        }
      },
      fail: (err) => {
        // Upload request failed
        console.error('File upload failed:', err)
        error.value = true
        onError?.(err)
      },
      complete: () => {
        // Runs regardless of success or failure
        loading.value = false
        onComplete?.()
      },
    })

    // Listen for upload progress
    uploadTask.onProgressUpdate((res) => {
      progress.value = res.progress
      onProgress?.(res.progress)
    })
  }
  catch (err) {
    // Failed to create the upload task
    console.error('Failed to create upload task:', err)
    error.value = true
    loading.value = false
    onError?.(new Error('Failed to create upload task'))
  }
}
