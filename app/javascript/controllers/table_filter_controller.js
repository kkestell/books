import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "filter" ]

  connect() {
    this.filterTargets.forEach((input) => {
      if (input.list) this.populateDatalist(input)
    })

    this.observer = new MutationObserver(() => this.filter())
    for (const body of this.element.tBodies) {
      this.observer.observe(body, { childList: true })
    }
  }

  disconnect() {
    this.observer.disconnect()
  }

  filter() {
    const filters = this.filterTargets
      .map((input) => ({ column: input.closest("th").cellIndex, value: input.value.trim().toLowerCase() }))
      .filter((filter) => filter.value !== "")

    for (const row of this.element.tBodies[0].rows) {
      row.hidden = filters.some((filter) =>
        !row.cells[filter.column].textContent.toLowerCase().includes(filter.value))
    }
  }

  populateDatalist(input) {
    const column = input.closest("th").cellIndex
    const values = new Set()

    for (const row of this.element.tBodies[0].rows) {
      const value = row.cells[column].dataset.filterValue ?? row.cells[column].textContent.trim()
      if (value !== "") values.add(value)
    }

    const options = document.createDocumentFragment()
    for (const value of Array.from(values).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))) {
      const option = document.createElement("option")
      option.value = value
      options.append(option)
    }
    input.list.append(options)
  }
}
