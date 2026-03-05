(function () {
  var OVERLAY_ID = 'formcoder-overlay';
  var FORM_ID = 'formcoder-form';
  var CANCEL_ID = 'formcoder-cancel';
  var TRIGGER_CLASS = 'formcoder-trigger';
  var TOOLBAR_SELECTOR = '.formcode-ace-editor-toolbar';

  // Build and append overlay once
  function createOverlay() {
    if (document.getElementById(OVERLAY_ID)) return;

    // inject minimal stylesheet for trigger alignment if needed
    if (!document.getElementById('formcoder-trigger-style')) {
      var style = document.createElement('style');
      style.id = 'formcoder-trigger-style';
      style.type = 'text/css';
      // float right and ensure following editor clears floats to avoid layout overlap
      style.appendChild(document.createTextNode('.formcoder-trigger-right{float:right;margin-left:8px;} .formcoder-trigger-right + .code-editor-wrapper{clear:both;}'));
      (document.head || document.getElementsByTagName('head')[0]).appendChild(style);
    }

    var overlay = document.createElement('div');
    overlay.id = OVERLAY_ID;
    overlay.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;';

    overlay.innerHTML = [
      '<div style="background:#fff;width:800px;max-width:92%;max-height:80vh;overflow:auto;padding:20px;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);border-radius:4px;box-sizing:border-box;">',
      '<h5>Form Coder</h5>',
      '<form id="' + FORM_ID + '" method="post">',
      '<textarea name="snippet" placeholder="Enter snippet" rows="12" style="width:100%;margin-bottom:10px;box-sizing:border-box;font-family:inherit;font-size:inherit;"></textarea>',
      '<div style="text-align:right;">',
      '<button type="button" class="button secondary small" id="' + CANCEL_ID + '">Cancel</button>',
      '<button type="submit" class="button primary small">Insert</button>',
      '</div>',
      '</form>',
      '</div>'
    ].join('');

    document.body.appendChild(overlay);

    // Close when clicking backdrop
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) overlay.style.display = 'none';
    });

    // Cancel button
    var cancel = overlay.querySelector('#' + CANCEL_ID);
    if (cancel) cancel.addEventListener('click', function () { overlay.style.display = 'none'; });

    // Set form action dynamically based on current path
    var form = overlay.querySelector('#' + FORM_ID);
    setFormAction(form);

    // Wire submit
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitForm(form, overlay);
    });
  }

  // Helper: normalize a possibly-relative URL against window.location.origin
  function normalizeUrl(url) {
    try {
      return (new URL(url, window.location.origin)).toString();
    } catch (e) {
      return url;
    }
  }

  // Helper: prefer a server-rendered data attribute if present. We look first on
  // the overlay form, then on any form on the page with the attribute.
  function getAiFormcoderUrlFromPage(form) {
    try {
      if (form && form.dataset && form.dataset.aiFormcoderUrl) {
        return normalizeUrl(form.dataset.aiFormcoderUrl);
      }
      var hostForm = document.querySelector('form[data-ai-formcoder-url]');
      if (hostForm && hostForm.dataset && hostForm.dataset.aiFormcoderUrl) {
        return normalizeUrl(hostForm.dataset.aiFormcoderUrl);
      }
    } catch (e) {
      // ignore
    }
    return null;
  }

  // Compute and set the form action so it always targets the collection's
  // formcoder endpoint (e.g. /.../forms/formcoder). Handles paths ending in
  // /new or /.../form/<name>/edit etc.
  function setFormAction(form) {
    try {
      var aiUrl = getAiFormcoderUrlFromPage(form);
      if (aiUrl) {
        try { form.action = aiUrl; } catch (e) { /* ignore */ }
        return;
      }

      var path = window.location.pathname.replace(/\/$/, '');

      // If we're on a single form edit/show path like /.../form/<name> or
      // /.../form/<name>/edit, replace with /.../forms
      if (/\/form\/[^^\/]+(\/edit)?$/.test(path) || /\/form\/[^^\/]+$/.test(path)) {
        path = path.replace(/\/form\/[^^\/]+(\/edit)?$/, '/forms');
      } else {
        // Remove trailing /new or /edit
        path = path.replace(/\/new$/, '').replace(/\/edit$/, '');
        // If the path ends with /form, convert to /forms
        path = path.replace(/\/form$/, '/forms');
        // If there's a /forms segment somewhere, prefer the canonical prefix up to it
        var m = path.match(/^(.*\/forms)(\/.*)?$/);
        if (m) path = m[1];
      }

      form.action = path + '/formcoder';
    } catch (e) {
      form.action = '/formcoder';
    }
  }

  // Submit the overlay form via fetch and place returned text into the target Ace editor
  function submitForm(form, overlay) {
    try { setFormAction(form); } catch (e) { /* ignore */ }

    var fd = new FormData(form);
    var action = form.getAttribute('action') || form.action || '/formcoder';

    fetch(action, { method: 'POST', body: fd, credentials: 'same-origin' })
      .then(function (resp) {
        if (!resp.ok) throw new Error('Network response was not ok: ' + resp.status);
        return resp.text();
      })
      .then(function (text) {
        var aceEl = overlay._aceEditor;
        if (aceEl) {
          trySetAceValue(aceEl, text);
        }
        overlay.style.display = 'none';
      })
      .catch(function (err) {
        console.error('formcoder POST failed', err);
      });
  }

  function trySetAceValue(aceEl, text) {
    var ta;
    if (typeof ace !== 'undefined') {
      try {
        var editor = ace.edit(aceEl);
        if (editor && typeof editor.setValue === 'function') {
          editor.setValue(text, -1);
          return;
        }
        if (editor && editor.session && typeof editor.session.setValue === 'function') {
          editor.session.setValue(text);
          return;
        }
      } catch (e) {
        // fall through to textarea fallback
      }
    }

    // Fallback: try to set an inner textarea if present
    ta = aceEl.querySelector && aceEl.querySelector('textarea');
    if (ta) ta.value = text;
  }

  function findAceForToolbar(toolbar) {
    if (!toolbar) return null;

    // prefer an ancestor wrapper with class .code-editor-wrapper
    if (toolbar.closest) {
      var wrapper = toolbar.closest('.code-editor-wrapper');
      if (wrapper) {
        var aceEl = wrapper.querySelector && wrapper.querySelector('.ace_editor');
        if (aceEl) return aceEl;
        if (wrapper.classList && wrapper.classList.contains('ace_editor')) return wrapper;
      }
    }

    // fallback: look for a sibling/child ace_editor
    var parent = toolbar.parentNode;
    if (parent) {
      var found = parent.querySelector && parent.querySelector('.ace_editor');
      if (found) return found;
    }

    return null;
  }

  function makeTrigger(aceEl) {
    var btn = document.createElement('button');
    btn.type = 'button';
    // add a right-align helper class
    btn.className = 'button small secondary ' + TRIGGER_CLASS + ' formcoder-trigger-right';
    btn.textContent = 'AI Formcoder';
    btn._aceEditor = aceEl || null;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var overlay = document.getElementById(OVERLAY_ID);
      if (!overlay) return;
      overlay._aceEditor = btn._aceEditor;
      // ensure form action is recalculated if the URL changed
      var form = overlay.querySelector('#' + FORM_ID);
      if (form) setFormAction(form);
      overlay.style.display = 'block';
    });
    return btn;
  }

  function insertTriggers() {
    var toolbars = document.querySelectorAll(TOOLBAR_SELECTOR);
    if (!toolbars || toolbars.length === 0) return false;

    toolbars = Array.prototype.slice.call(toolbars);
    toolbars.forEach(function (toolbar) {
      // avoid duplicate triggers (either inside label or adjacent)
      if (toolbar.getAttribute('data-formcoder-added')) return;

      var label = (toolbar.closest && toolbar.closest('label')) || null;
      var aceEl = findAceForToolbar(toolbar);
      var btn = makeTrigger(aceEl);

      try {
        if (label && toolbar.parentNode) {
          // Insert the trigger directly before the toolbar element so it
          // appears after label-text / label-required but before the toolbar.
          toolbar.parentNode.insertBefore(btn, toolbar);

          // ensure the editor wrapper beneath clears floats so the editor
          // doesn't float next to the button
          try {
            if (aceEl && aceEl.closest) {
              var wrapper = aceEl.closest('.code-editor-wrapper');
              if (wrapper && wrapper.style) wrapper.style.clear = 'both';
            }
          } catch (e) { /* ignore */ }
        } else if (toolbar.parentNode) {
          // fallback: insert after the toolbar
          if (toolbar.nextSibling) {
            toolbar.parentNode.insertBefore(btn, toolbar.nextSibling);
          } else {
            toolbar.parentNode.appendChild(btn);
          }
        }

        toolbar.setAttribute('data-formcoder-added', '1');
      } catch (e) {
        try {
          toolbar.parentNode.appendChild(btn);
          toolbar.setAttribute('data-formcoder-added', '1');
        } catch (e) {
          // ignore
        }
      }
    });

    return true;
  }

  function init() {
    createOverlay();
    if (insertTriggers()) return;

    var attempts = 0;
    var maxAttempts = 20;
    var iv = setInterval(function () {
      attempts++;
      if (insertTriggers() || attempts >= maxAttempts) clearInterval(iv);
    }, 250);

    // observe DOM to catch dynamically added toolbars
    if (typeof MutationObserver !== 'undefined') {
      var observer = new MutationObserver(function () {
        insertTriggers();
      });
      observer.observe(document.documentElement || document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
