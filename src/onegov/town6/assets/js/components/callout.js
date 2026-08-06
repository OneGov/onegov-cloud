const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host {
      display: block;
      border-radius: 4px;
      padding: 1rem;
      margin: 1rem 0;
      border-left: 4px solid var(--accent, #2196f3);
      background: color-mix(in srgb, var(--accent, #2196f3) 8%, transparent);
    }

    :host([type="alert"])   { --accent: #cc4b37; }
    :host([type="success"]) { --accent: #3adb76; }
    :host([type="warning"]) { --accent: #ffae00; }

    .title {
      font-weight: bold;
      margin-bottom: .25rem;
    }
  </style>

  <div class="title"><slot name="title"></slot></div>
  <div class="body"><slot></slot></div>
`;

class OGCallout extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' })
      .appendChild(template.content.cloneNode(true));
  }
}

customElements.define('og-callout', OGCallout);