// Enum definitions

export enum TestEnum {
  A = '1',
  B = '2',
}

// uni.uploadFile file upload parameters
export interface IUniUploadFileOptions {
  file?: File
  files?: UniApp.UploadFileOptionFiles[]
  filePath?: string
  name?: string
  formData?: any
}
