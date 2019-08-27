if (!RedactorPlugins) var RedactorPlugins = {};
 
RedactorPlugins.bufferbuttons = function()
{
    return {
        init: function()
        {
            var undo = this.button.addFirst('undo', this.opts.langs[this.opts.lang].undo);
            var redo = this.button.addAfter('undo', 'redo', this.opts.langs[this.opts.lang].redo);
 
            this.button.addCallback(undo, this.buffer.undo);
            this.button.addCallback(redo, this.buffer.redo);
        }
    };
};