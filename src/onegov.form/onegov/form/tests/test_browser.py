def test_snippets(browser):
    browser.visit('/snippets')

    assert browser.is_element_present_by_css('.formcode-snippets')
    assert len(browser.find_by_css('.formcode-toolbar')) == 1

    assert not browser.find_by_css('.formcode-snippet')
    browser.find_by_css('.formcode-toolbar-element').click()

    assert browser.find_by_css('.formcode-snippet')
    browser.find_by_css('.formcode-toolbar-element').click()

    assert not browser.find_by_css('.formcode-snippet')
    browser.find_by_css('.formcode-toolbar-element').click()

    browser.find_by_css('.formcode-snippet-optional').click()
    assert '= ___' in browser.find_by_css('textarea').value

    assert not browser.find_by_css('.formcode-snippet')
    browser.find_by_css('.formcode-toolbar-element').click()

    browser.find_by_css('.formcode-snippet-required').click()
    assert '*= ___' in browser.find_by_css('textarea').value


def test_registry(browser):
    browser.visit('/registry')
    browser.wait_for_js_variable('formcodeWatcherRegistry')
    browser.execute_script("""
        var watcher = formcodeWatcherRegistry.new("test");
        var unsubscribe = watcher.subscribe(function(value) {
            window.code = value;
        });
        watcher.update("Label = ...");
        unsubscribe();
        watcher.update("Label = ___");
    """)

    code = browser.evaluate_script("window.code")
    assert code == [{'human_id': 'Label', 'type': 'textarea', 'id': 'label'}]


def test_formcode_format(browser):
    browser.visit('/formcode-format')
    browser.wait_for_js_variable('formcodeWatcherRegistry')
    browser.execute_script("""
        var watcher = formcodeWatcherRegistry.new("test");
        var el = document.querySelector('#container');

        el.setAttribute('data-watcher', 'test');
        el.setAttribute('data-target', 'textarea');

        initFormcodeFormat(el);

        watcher.update('Textfield = ___');
    """)

    browser.find_by_css('.formcode-toolbar-element').click()
    browser.find_by_css('.formcode-format-field').click()

    assert browser.find_by_css('textarea').value == '[Textfield]'
