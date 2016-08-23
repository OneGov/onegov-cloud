define("ace/mode/form_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

var escapeRe = "\\\\(?:[\\\\0abtrn;#=:]|x[a-fA-F\\d]{4})";

var FormHighlightRules = function() {
    this.$rules = {
        start: [
            {
                token: 'comment',
                regex: '^#.*'
            },
            {
                token: 'support.function',
                regex: /(___|\*\*\*|\.\.\.|@@@|YYYY.MM.DD|YYYY.MM.DD HH:MM|HH:MM)/
            },
            {
                token: 'keyword',
                regex: /[\[\(]{1}[x ]?[\]\)]{1}/
            },
            {
                token: 'keyword.operator',
                regex: /(\*\s?=|=)/
            },
            {
                token: 'support.type',
                regex: /# .*$/
            },
            {
                token: 'string',
                regex: /(\*\.\*|\*\.[a-zA-Z\.0-9]+)/
            },
            {
                token: 'support.constant',
                regex: /\[[0-9]+\]/
            }
        ]
    };

    this.normalizeRules();
};

FormHighlightRules.metaData = {
    fileTypes: ['form'],
    keyEquivalent: '^~F',
    name: 'Form'
};

oop.inherits(FormHighlightRules, TextHighlightRules);

exports.FormHighlightRules = FormHighlightRules;
});

define("ace/mode/form",["require","exports","module","ace/lib/oop","ace/mode/text","ace/mode/form_highlight_rules"], function(require, exports, module) {
"use strict";

var oop = require("../lib/oop");
var TextMode = require("./text").Mode;
var FormHighlightRules = require("./form_highlight_rules").FormHighlightRules;

var Mode = function() {
    this.HighlightRules = FormHighlightRules;
};
oop.inherits(Mode, TextMode);

(function() {
    this.$id = "ace/mode/form";
}).call(Mode.prototype);

exports.Mode = Mode;
});