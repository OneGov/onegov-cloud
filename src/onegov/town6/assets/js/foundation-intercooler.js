// Reinitialize Foundation whenever an element has been reloaded via
// intercooler because otherwise the foundation components won't work.
Intercooler.ready((elt) => {
    console.log('reinitFoundation', elt);
    if (elt.data('reinitFoundation') !== null) {
        elt.foundation();
        Foundation.Triggers.Initializers.addClosemeListener();
    }
});
