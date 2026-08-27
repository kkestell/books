import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "input", "selection", "submit", "upload", "uploadBar", "uploadStatus" ]

  connect() {
    this.uploads = new Map()
    this.completedUploads = 0
    this.selectionChanged()
  }

  selectionChanged() {
    const files = this.inputTargets.flatMap((input) => Array.from(input.files))
    const totalBytes = files.reduce((sum, file) => sum + file.size, 0)

    this.submitTarget.disabled = files.length === 0
    this.selectionTarget.textContent = files.length === 0
      ? "No ebooks selected."
      : `${files.length} ebook${files.length === 1 ? "" : "s"} selected (${this.formatBytes(totalBytes)}).`
  }

  uploadInitialized(event) {
    const { id, file } = event.detail
    this.uploads.set(id, { size: file.size, progress: 0 })
    this.uploadTarget.hidden = false
    this.submitTarget.disabled = true
    this.renderUploadProgress()
  }

  uploadProgress(event) {
    const upload = this.uploads.get(event.detail.id)
    if (!upload) return

    upload.progress = event.detail.progress
    this.renderUploadProgress()
  }

  uploadEnded(event) {
    const upload = this.uploads.get(event.detail.id)
    if (upload) upload.progress = 100
    this.completedUploads += 1
    this.renderUploadProgress()
  }

  renderUploadProgress() {
    const uploads = Array.from(this.uploads.values())
    const totalBytes = uploads.reduce((sum, upload) => sum + upload.size, 0)
    const uploadedBytes = uploads.reduce((sum, upload) => sum + upload.size * upload.progress / 100, 0)
    const percentage = totalBytes === 0 ? 0 : Math.round(uploadedBytes * 100 / totalBytes)

    this.uploadBarTarget.value = percentage
    this.uploadBarTarget.textContent = `${percentage}%`
    this.uploadStatusTarget.textContent = this.completedUploads === uploads.length && uploads.length > 0
      ? "Uploads complete. Starting background import…"
      : `Uploading ebooks… ${percentage}%`
  }

  formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
    return `${(bytes / 1024 ** 3).toFixed(1)} GB`
  }
}
