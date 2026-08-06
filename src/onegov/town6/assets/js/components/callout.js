// og-callout — a small demo of the native Web Components APIs:
//   * a Custom Element (customElements.define)
//   * a Shadow DOM for style + markup encapsulation
//   * <slot> for projecting the page's content into the component
//   * an attribute (`type`) that drives styling via :host()
//
// The styles live entirely inside the shadow root, so nothing here
// leaks out and nothing from the page leaks in

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host {
      --accent: #2196f3;
      display: block;
      border-radius: .7rem;
      padding: 1rem;
      margin: 1rem 0;
      border-left: 4px solid var(--accent);
      background: color-mix(in srgb, var(--accent) 12%, transparent);
    }

    /* the attribute on the host element selects the accent color */
    :host([type="success"]) { --accent: #237f35; }
    :host([type="warning"]) { --accent: #d59200; }
    :host([type="alert"])   { --accent: #b2232f; }
    :host([type="info"])    { --accent: #1a52a5; }

    .title {
      font-weight: bold;
      margin-bottom: .25rem;
    }

    /* show the title row only when a title was slotted in */
    .title { display: none; }
    :host(:has([slot="title"])) .title { display: block; }
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
