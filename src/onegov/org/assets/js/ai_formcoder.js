(function() {
    var OVERLAY_ID = 'formcoder-overlay';
    var FORM_ID = 'formcoder-form';
    var CANCEL_ID = 'formcoder-cancel';
    var TRIGGER_CLASS = 'formcoder-trigger';
    var TOOLBAR_SELECTOR = '.formcode-ace-editor-toolbar';
    var LOADING_CLASS = 'formcoder-loading';

    function normalizeUrl(url) {
        try {
            return (new URL(url, window.location.origin)).toString();
        } catch (e) {
            return url;
        }
    }

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

    function setFormAction(form) {
        try {
            var aiUrl = getAiFormcoderUrlFromPage(form);
            if (aiUrl) {
                form.action = aiUrl;
                return;
            }

            var path = window.location.pathname.replace((/\/$/), '');
            if ((/\/form\/[^^\/]+(\/edit)?$/).test(path) || (/\/form\/[^^\/]+$/).test(path)) {
                path = path.replace((/\/form\/[^^\/]+(\/edit)?$/), '/forms');
            } else {
                path = path.replace((/\/new$/), '').replace((/\/edit$/), '');
                path = path.replace((/\/form$/), '/forms');
                var m = path.match((/^(.*\/forms)(\/.*)?$/));
                if (m) {
                    path = m[1];
                }
            }
            form.action = path + '/formcoder';
        } catch (e) {
            form.action = '/formcoder';
        }
    }

    function trySetAceValue(aceEl, text) {
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
                // ignore
            }
        }
        var ta = aceEl.querySelector && aceEl.querySelector('textarea');
        if (ta) {
            ta.value = text;
        }
    }

    function submitForm(form, overlay) {
        var submit = form.querySelector('[type="submit"]');

        function setLoading(loading) {
            if (!submit) {
                return;
            }
            submit.disabled = loading;
            if (loading) {
                submit.classList.add(LOADING_CLASS);
            } else {
                submit.classList.remove(LOADING_CLASS);
            }
        }

        try {
            setFormAction(form);
        } catch (e) {
            // ignore
        }
        setLoading(true);
        var fd = new FormData(form);
        var action = form.getAttribute('action') || form.action || '/formcoder';
        fetch(action, {method: 'POST', body: fd, credentials: 'same-origin'})
            .then(function(resp) {
                if (!resp.ok) {
                    throw new Error(resp.status);
                }
                return resp.text();
            })
            .then(function(text) {
                setLoading(false);
                var aceEl = overlay._aceEditor;
                if (aceEl) {
                    trySetAceValue(aceEl, text);
                }
                overlay.style.display = 'none';
            })
            .catch(function(err) {
                setLoading(false);
                console.error('formcoder POST failed', err); // eslint-disable-line no-console
            });
    }

    function createOverlay() {
        if (document.getElementById(OVERLAY_ID)) {
            return;
        }

        if (!document.getElementById('formcoder-styles')) {
            var style = document.createElement('style');
            style.id = 'formcoder-styles';
            style.textContent = [
                '@keyframes formcoder-spin { to { transform: rotate(360deg); } }',
                '.' + LOADING_CLASS + ' { opacity: .65; pointer-events: none; }',
                '.' + LOADING_CLASS + '::after {',
                '  content: ""; display: inline-block; vertical-align: middle;',
                '  width: .75em; height: .75em; margin-left: .4em;',
                '  border: 2px solid; border-top-color: transparent; border-radius: 50%;',
                '  animation: formcoder-spin .7s linear infinite;',
                '}'
            ].join('\n');
            document.head.appendChild(style);
        }

        var overlay = document.createElement('div');
        overlay.id = OVERLAY_ID;
        overlay.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:9999;';

        overlay.innerHTML = [
            '<div style="background:#fff;width:800px;max-width:92%;max-height:80vh;overflow:auto;padding:20px;position:absolute;top:50%;left:40%;transform:translate(-50%,-50%);border-radius:4px;box-sizing:border-box;">',
            '<h5>Formcoder</h5>',
            '<form id="' + FORM_ID + '" method="post">',
            '<textarea name="snippet" placeholder="What fields for the form you need?" rows="12" style="width:100%;margin-bottom:10px;box-sizing:border-box;font-family:inherit;font-size:inherit;"></textarea>',
            '<div style="text-align:right;">',
            '<button type="button" class="button hollow" id="' + CANCEL_ID + '">Cancel</button>',
            '<button type="submit" class="button" style="margin-left: 8px">Generate Form Code</button>',
            '</div>',
            '</form>',
            '</div>'
        ].join('');

        document.body.appendChild(overlay);

        // Localize overlay text at creation-time as a best-effort
        // declare once so variables are available outside try/catch (linters)
        var locale, ta, cancelBtn, submitBtn;
        try {
            if (typeof window !== 'undefined' && typeof window.locale === 'function') {
                locale = window.locale;
            } else {
                locale = function(s) { return s; };
            }

            ta = overlay.querySelector('textarea[name="snippet"]');
            if (ta) {
                ta.placeholder = locale('What fields for the form you need?');
            }

            cancelBtn = overlay.querySelector('#' + CANCEL_ID);
            if (cancelBtn) {
                cancelBtn.textContent = locale('Cancel');
            }

            submitBtn = overlay.querySelector('#' + FORM_ID + ' [type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = locale('Generate Form Code');
            }
        } catch (e) {
            // ignore localization failures
        }

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                overlay.style.display = 'none';
            }
        });

        cancelBtn = cancelBtn || overlay.querySelector('#' + CANCEL_ID);
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                overlay.style.display = 'none';
            });
        }

        var form = overlay.querySelector('#' + FORM_ID);
        setFormAction(form);
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm(form, overlay);
        });
    }

    function findAceForToolbar(toolbar) {
        if (!toolbar) {
            return null;
        }
        var wrapper = toolbar.closest('.code-editor-wrapper');
        if (wrapper) {
            var aceEl = wrapper.querySelector('.ace_editor');
            if (aceEl) {
                return aceEl;
            }
            if (wrapper.classList && wrapper.classList.contains('ace_editor')) {
                return wrapper;
            }
        }
        var parent = toolbar.parentNode;
        if (parent) {
            var found = parent.querySelector('.ace_editor');
            if (found) {
                return found;
            }
        }
        return null;
    }

    function makeTrigger(aceEl) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'button secondary ' + TRIGGER_CLASS + ' formcoder-trigger';
        btn.style.cssText = 'display:inline-block;width:auto;position:relative;z-index:1;';
        btn.textContent = 'AI Formcoder';
        btn._aceEditor = aceEl || null;
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            var overlay = document.getElementById(OVERLAY_ID);
            if (!overlay) {
                return;
            }

            overlay._aceEditor = btn._aceEditor;
            var form = overlay.querySelector('#' + FORM_ID);
            if (form) {
                setFormAction(form);
            }
            overlay.style.display = 'block';
        });
        return btn;
    }

    function insertTriggers() {
        var toolbars = document.querySelectorAll(TOOLBAR_SELECTOR);
        if (!toolbars || toolbars.length === 0) {
            return false;
        }
        Array.prototype.slice.call(toolbars).forEach(function(toolbar) {
            if (toolbar.getAttribute('data-formcoder-added')) {
                return;
            }
            var aceEl = findAceForToolbar(toolbar);
            var btn = makeTrigger(aceEl);
            var anchor = toolbar.closest('label') || toolbar;
            anchor.parentNode.insertBefore(btn, anchor);
            toolbar.setAttribute('data-formcoder-added', '1');
        });
        return true;
    }

    function init() {
        createOverlay();
        insertTriggers();
        if (typeof MutationObserver !== 'undefined') {
            var observer = new MutationObserver(function() {
                insertTriggers();
            });
            observer.observe(document.documentElement || document.body, {childList: true, subtree: true});
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
