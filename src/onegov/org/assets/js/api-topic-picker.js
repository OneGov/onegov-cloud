/*
    Lets editors pick a topic of the source organisation through its API.

    Starts with the root topics and only loads the children of a topic once
    the editor navigates into it. The id of the selected topic is written
    into the hidden input given by `data-input`, its title is shown as
    placeholder of the title input given by `data-title-input`.
*/
(function() {
    'use strict';

    function element(tag, className, text) {
        var el = document.createElement(tag);
        if (className) {
            el.className = className;
        }
        if (text !== undefined) {
            el.textContent = text;
        }
        return el;
    }

    function parseItems(json) {
        var collection = json.collection || {};
        var items = (collection.items || []).map(function(item) {
            var data = {};
            (item.data || []).forEach(function(d) {
                data[d.name] = d.value;
            });
            return {
                id: item.href.replace(/\/+$/, '').split('/').pop(),
                title: data.title,
                lead: data.lead,
                trait: data.trait
            };
        });
        var next = (collection.links || []).filter(function(link) {
            return link.rel === 'next' && link.href;
        })[0];
        return {items: items, next: next ? next.href : null};
    }

    function ApiTopicPicker(root) {
        this.root = root;
        this.apiUrl = root.dataset.apiUrl.replace(/\/?$/, '/');
        this.input = document.getElementById(root.dataset.input);
        this.titleInput = document.getElementById(root.dataset.titleInput);
        this.labels = JSON.parse(root.dataset.labels);
        this.selectedTitle = root.dataset.selectedTitle || null;
        // the path of topics the editor navigated into
        this.path = [];

        this.selected = element('p', 'api-topic-picker-selected');
        this.breadcrumbs = element('ul', 'breadcrumbs api-topic-picker-path');
        this.list = element('ul', 'api-topic-picker-list');
        // links instead of buttons, as the picker is rendered inside the
        // label of the field, which forwards hovers and clicks to the first
        // button inside of it
        this.more = element('a', 'button secondary', this.labels.more);
        this.more.href = '#';
        this.message = element('p', 'api-topic-picker-message');

        root.appendChild(this.selected);
        root.appendChild(this.breadcrumbs);
        root.appendChild(this.list);
        root.appendChild(this.message);
        root.appendChild(this.more);

        this.renderSelected();
        this.navigate([]);
    }

    ApiTopicPicker.prototype.renderSelected = function() {
        this.selected.textContent = '';
        if (this.input.value && this.selectedTitle) {
            this.selected.appendChild(
                document.createTextNode(this.labels.selected + ': ')
            );
            this.selected.appendChild(
                element('strong', null, this.selectedTitle)
            );
            if (this.titleInput) {
                this.titleInput.placeholder = this.selectedTitle;
            }
        } else {
            this.selected.textContent = this.labels.none_selected;
        }
    };

    ApiTopicPicker.prototype.renderBreadcrumbs = function() {
        var self = this;
        this.breadcrumbs.textContent = '';

        var crumbs = [{id: null, title: this.labels.back}].concat(this.path);
        crumbs.forEach(function(crumb, index) {
            var li = element('li');
            if (index === crumbs.length - 1) {
                li.className = 'current';
                li.textContent = crumb.title;
            } else {
                var a = element('a', null, crumb.title);
                a.href = '#';
                a.addEventListener('click', function(e) {
                    e.preventDefault();
                    self.navigate(self.path.slice(0, index));
                });
                li.appendChild(a);
            }
            self.breadcrumbs.appendChild(li);
        });
    };

    ApiTopicPicker.prototype.navigate = function(path) {
        var parent = path.length ? path[path.length - 1].id : 'root';
        this.path = path;
        this.list.textContent = '';
        this.renderBreadcrumbs();
        this.load(this.apiUrl + 'topics?parent=' + encodeURIComponent(parent));
    };

    ApiTopicPicker.prototype.load = function(url) {
        var self = this;
        this.more.style.display = 'none';
        this.message.textContent = this.labels.loading;

        fetch(url, {headers: {'Accept': 'application/vnd.collection+json'}})
            .then(function(response) {
                if (!response.ok) {
                    throw new Error(response.status);
                }
                return response.json();
            })
            .then(function(json) {
                var result = parseItems(json);
                result.items.forEach(function(item) {
                    // links and iframes can't be linked
                    if (item.trait === 'page') {
                        self.list.appendChild(self.renderItem(item));
                    }
                });

                self.message.textContent = self.list.children.length ?
                    '' : self.labels.empty;

                if (result.next) {
                    self.more.style.display = '';
                    self.more.onclick = function(e) {
                        e.preventDefault();
                        self.load(result.next);
                    };
                }
            })
            .catch(function() {
                self.message.textContent = self.labels.error;
            });
    };

    ApiTopicPicker.prototype.renderItem = function(item) {
        var self = this;
        var li = element('li');
        if (item.id === this.input.value) {
            li.className = 'is-selected';
        }

        var title = element('span', 'api-topic-picker-title', item.title);
        li.appendChild(title);

        var actions = element('span', 'api-topic-picker-actions');

        var select = element('a', 'button button-select', this.labels.select);
        select.href = '#';
        select.addEventListener('click', function(e) {
            e.preventDefault();
            self.input.value = item.id;
            self.selectedTitle = item.title;
            self.renderSelected();
            [].forEach.call(self.list.children, function(child) {
                child.classList.remove('is-selected');
            });
            li.classList.add('is-selected');
        });
        actions.appendChild(select);

        var children = element(
            'a', 'api-topic-picker-children', this.labels.children + ' ›'
        );
        children.href = '#';
        children.addEventListener('click', function(e) {
            e.preventDefault();
            self.navigate(self.path.concat([item]));
        });
        actions.appendChild(children);

        li.appendChild(actions);
        return li;
    };

    function setup() {
        [].forEach.call(
            document.querySelectorAll('.api-topic-picker'),
            function(root) { new ApiTopicPicker(root); }
        );
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
