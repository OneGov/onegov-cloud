const jsdomUnmocked = require('jsdom');
const d3 = require('../d3');
const fs = require('fs');

module.exports = {
    jsdom: function() {
        var document = jsdomUnmocked.jsdom();

        var oldCreateElementNS = document.createElementNS;
        document.createElementNS = function(ns, tagName) {
            var elem = oldCreateElementNS.call(this, ns, tagName);
            elem.getBBox = function () {
                var fontSize = parseInt(elem.style.fontSize, 10) || 0;
                var height = Math.max(
                    parseInt(elem.getAttribute('height'), 10) || 0,
                    fontSize < 24 ? fontSize + 3 : Math.round(fontSize * 1.2)
                );
                var width = Math.max(
                    parseInt(elem.getAttribute('width'), 10) || 0,
                    elem.textContent.length * fontSize * 0.55
                );
                return {x: 0, y: 0, width: width, height: height};
            };
            elem.getComputedTextLength = function() {
                var fontSize = parseInt(elem.style.fontSize, 10) || 0;
                var width = Math.max(
                    parseInt(elem.getAttribute('width'), 10) || 0,
                    elem.textContent.length * fontSize * 0.55
                );
                return width;
            };
            return elem;
        };

        document.svg = function() {
            var svg = '';
            elements = this.body.getElementsByTagName('svg');
            if (elements.length) {
                svg = d3.select(elements[0]).node().outerHTML;
            }
            return svg;
        };

        document.save_svg = function() {
            fs.writeFile('test.svg', this.svg());
        };

        return document;
    }
};
