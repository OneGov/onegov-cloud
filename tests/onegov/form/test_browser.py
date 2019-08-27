from time import sleep


def test_snippets(browser):
    browser.visit('/snippets')
    browser.wait_for_js_variable('initFormSnippets')
    browser.execute_script("""
        initFormSnippets(document.querySelector('.formcode-snippets'));
    """)

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

    browser.wait_for_js_variable('window.code')
    code = browser.evaluate_script("window.code")
    assert code == [{'human_id': 'Label', 'type': 'textarea', 'id': 'label'}]


def test_formcode_format(browser):
    browser.visit('/formcode-format')
    browser.wait_for_js_variable('initFormcodeFormat')
    browser.execute_script("""
        var watcher = formcodeWatcherRegistry.new("test");
        var el = document.querySelector('#container');

        el.setAttribute('data-watcher', 'test');
        el.setAttribute('data-target', 'textarea');

        initFormcodeFormat(el);

        watcher.update('Textfield = ___');
    """)

    browser.find_by_css('.formcode-toolbar-element').click()
    browser.find_by_css('.formcode-snippet').click()

    assert browser.find_by_css('textarea').value == '[Textfield]'


def test_formcode_select_empty(browser):
    browser.visit('/formcode-select')
    browser.wait_for_js_variable('initFormcodeSelect')
    browser.driver.execute_script("""
        var watcher = formcodeWatcherRegistry.new();
        var el = document.querySelector('#container');

        initFormcodeSelect(el, watcher, 'textarea', ['text', 'textarea']);
        watcher.update(arguments[0]);
    """, 'A = ___\nB = ...\nC = *.png')

    assert len(browser.find_by_css('.formcode-select input')) == 2
    browser.find_by_css('.formcode-select input')[0].click()
    browser.find_by_css('.formcode-select input')[1].click()

    assert browser.find_by_css('textarea').value == "A\nB"

    browser.find_by_css('.formcode-select input')[1].click()
    assert browser.find_by_css('textarea').value == "A"

    browser.find_by_css('.formcode-select input')[1].click()
    assert browser.find_by_css('textarea').value == "A\nB"

    browser.find_by_css('.formcode-select input')[0].click()
    assert browser.find_by_css('textarea').value == "B"

    browser.find_by_css('.formcode-select input')[1].click()
    assert browser.find_by_css('textarea').value == ""


def test_formcode_select_prefilled(browser):
    browser.visit('/formcode-select')
    browser.wait_for_js_variable('initFormcodeSelect')
    browser.driver.execute_script("""
        var watcher = formcodeWatcherRegistry.new();
        var el = document.querySelector('#container');
        document.querySelector('textarea').value='A'

        initFormcodeSelect(el, watcher, 'textarea', ['text', 'textarea']);
        watcher.update(arguments[0]);
    """, 'A = ___\nB = ...\nC = *.png')

    assert len(browser.find_by_css('.formcode-select input:checked')) == 1


def test_formcode_keep_selection(browser):
    browser.visit('/formcode-select')
    browser.wait_for_js_variable('initFormcodeSelect')
    browser.driver.execute_script("""
        var watcher = document.watcher = formcodeWatcherRegistry.new();
        var el = document.querySelector('#container');
        document.querySelector('textarea').value='A'

        initFormcodeSelect(el, watcher, 'textarea', ['text', 'textarea']);
        watcher.update('B = ___');
    """)

    assert len(browser.find_by_css('.formcode-select input:checked')) == 0
    browser.driver.execute_script("document.watcher.update('A = ___');")

    sleep(0.1)

    assert len(browser.find_by_css('.formcode-select input:checked')) == 1
    browser.driver.execute_script("document.watcher.update('C = ___');")

    sleep(0.1)

    assert len(browser.find_by_css('.formcode-select input:checked')) == 0


def test_field_errors_should_not_yield_updates(browser):
    browser.visit('/formcode-format')
    browser.wait_for_js_variable('initFormcodeFormat')
    browser.execute_script("""
        document.watcher = formcodeWatcherRegistry.new();
        var el = document.querySelector('#container')

        initFormcodeFormat(el, document.watcher, 'textarea');
        document.watcher.update('Textfield = ___');
    """)

    browser.find_by_css('.formcode-toolbar-element').click()

    assert len(browser.find_by_css('.formcode-snippet')) == 1
    assert browser.find_by_css('.formcode-snippet').text == "Textfield"

    browser.execute_script("document.watcher.update('Test =-= !invalid');")

    assert len(browser.find_by_css('.formcode-snippet')) == 1
    assert browser.find_by_css('.formcode-snippet').text == "Textfield"

    browser.execute_script("document.watcher.update('Fixed = ___');")

    assert len(browser.find_by_css('.formcode-snippet')) == 1
    assert browser.find_by_css('.formcode-snippet').text == "Fixed"
