(function () {
  var OVERLAY_ID = 'formcoder-overlay';
  var FORM_ID = 'formcoder-form';
  var CANCEL_ID = 'formcoder-cancel';
  var TRIGGER_CLASS = 'formcoder-trigger';
  var TOOLBAR_SELECTOR = '.formcode-ace-editor-toolbar';

  function createOverlay() {
    if (document.getElementById(OVERLAY_ID)) return;

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

    overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.style.display = 'none'; });
    var cancel = overlay.querySelector('#' + CANCEL_ID);
    if (cancel) cancel.addEventListener('click', function () { overlay.style.display = 'none'; });

    var form = overlay.querySelector('#' + FORM_ID);
    setFormAction(form);
    form.addEventListener('submit', function (e) { e.preventDefault(); submitForm(form, overlay); });
  }

  function normalizeUrl(url) {
    try { return (new URL(url, window.location.origin)).toString(); } catch (e) { return url; }
  }

  function getAiFormcoderUrlFromPage(form) {
    try {
      if (form && form.dataset && form.dataset.aiFormcoderUrl) return normalizeUrl(form.dataset.aiFormcoderUrl);
      var hostForm = document.querySelector('form[data-ai-formcoder-url]');
      if (hostForm && hostForm.dataset && hostForm.dataset.aiFormcoderUrl) return normalizeUrl(hostForm.dataset.aiFormcoderUrl);
    } catch (e) {}
    return null;
  }

  function setFormAction(form) {
    try {
      var aiUrl = getAiFormcoderUrlFromPage(form);
      if (aiUrl) { form.action = aiUrl; return; }

      var path = window.location.pathname.replace(/\/$/, '');
      if (/\/form\/[^^\/]+(\/edit)?$/.test(path) || /\/form\/[^^\/]+$/.test(path)) {
        path = path.replace(/\/form\/[^^\/]+(\/edit)?$/, '/forms');
      } else {
        path = path.replace(/\/new$/, '').replace(/\/edit$/, '');
        path = path.replace(/\/form$/, '/forms');
        var m = path.match(/^(.*\/forms)(\/.*)?$/);
        if (m) path = m[1];
      }
      form.action = path + '/formcoder';
    } catch (e) { form.action = '/formcoder'; }
  }

  function submitForm(form, overlay) {
    try { setFormAction(form); } catch (e) {}
    var fd = new FormData(form);
    var action = form.getAttribute('action') || form.action || '/formcoder';
    fetch(action, { method: 'POST', body: fd, credentials: 'same-origin' })
      .then(function (resp) { if (!resp.ok) throw new Error(resp.status); return resp.text(); })
      .then(function (text) { var aceEl = overlay._aceEditor; if (aceEl) trySetAceValue(aceEl, text); overlay.style.display = 'none'; })
      .catch(function (err) { console.error('formcoder POST failed', err); });
  }

  function trySetAceValue(aceEl, text) {
    if (typeof ace !== 'undefined') {
      try {
        var editor = ace.edit(aceEl);
        if (editor && typeof editor.setValue === 'function') { editor.setValue(text, -1); return; }
        if (editor && editor.session && typeof editor.session.setValue === 'function') { editor.session.setValue(text); return; }
      } catch (e) {}
    }
    var ta = aceEl.querySelector && aceEl.querySelector('textarea'); if (ta) ta.value = text;
  }

  function findAceForToolbar(toolbar) {
    if (!toolbar) return null;
    if (toolbar.closest) {
      var wrapper = toolbar.closest('.code-editor-wrapper');
      if (wrapper) { var aceEl = wrapper.querySelector && wrapper.querySelector('.ace_editor'); if (aceEl) return aceEl; if (wrapper.classList && wrapper.classList.contains('ace_editor')) return wrapper; }
    }
    var parent = toolbar.parentNode;
    if (parent) { var found = parent.querySelector && parent.querySelector('.ace_editor'); if (found) return found; }
    return null;
  }

  function makeTrigger(aceEl) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'button small secondary ' + TRIGGER_CLASS + ' formcoder-trigger';
    btn.style.cssText = 'float:right;margin-left:8px;display:inline-block;width:auto;';
    btn.textContent = 'AI Formcoder';
    btn._aceEditor = aceEl || null;
    btn.addEventListener('click', function (e) { e.stopPropagation(); var overlay = document.getElementById(OVERLAY_ID); if (!overlay) return; overlay._aceEditor = btn._aceEditor; var form = overlay.querySelector('#' + FORM_ID); if (form) setFormAction(form); overlay.style.display = 'block'; });
    return btn;
  }

  function insertTriggers() {
    var toolbars = document.querySelectorAll(TOOLBAR_SELECTOR);
    if (!toolbars || toolbars.length === 0) return false;
    Array.prototype.slice.call(toolbars).forEach(function (toolbar) {
      if (toolbar.getAttribute('data-formcoder-added')) return;
      var aceEl = findAceForToolbar(toolbar);
      var btn = makeTrigger(aceEl);
      toolbar.parentNode.insertBefore(btn, toolbar);
      toolbar.setAttribute('data-formcoder-added', '1');
    });
    return true;
  }

  function init() { createOverlay(); insertTriggers(); if (typeof MutationObserver !== 'undefined') { var observer = new MutationObserver(function () { insertTriggers(); }); observer.observe(document.documentElement || document.body, { childList: true, subtree: true }); } }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

})();
