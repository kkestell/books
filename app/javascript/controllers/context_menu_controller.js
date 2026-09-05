import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu", "edit", "download"]

  open(event) {
    const editUrl = event.currentTarget.dataset.contextMenuEditUrl
    const downloadUrl = event.currentTarget.dataset.contextMenuDownloadUrl
    if (!editUrl && !downloadUrl) return

    event.preventDefault()
    event.stopPropagation()

    this.returnFocus = event.currentTarget
    this.editTarget.href = editUrl
    this.downloadTarget.hidden = !downloadUrl
    if (downloadUrl) this.downloadTarget.href = downloadUrl
    this.menuTarget.hidden = false
    this.positionMenu(event.clientX, event.clientY)
    this.editTarget.focus()
  }

  close(event) {
    if (this.menuTarget.hidden) return

    this.menuTarget.hidden = true

    if (event?.type === "keydown") this.returnFocus?.focus()
    this.returnFocus = null
  }

  positionMenu(x, y) {
    const gutter = 8
    const bounds = this.menuTarget.getBoundingClientRect()
    const left = Math.max(gutter, Math.min(x, window.innerWidth - bounds.width - gutter))
    const top = Math.max(gutter, Math.min(y, window.innerHeight - bounds.height - gutter))

    this.menuTarget.style.left = `${left}px`
    this.menuTarget.style.top = `${top}px`
  }
}
