/**
 * Common features shared between staff and client chat.
 */
document.addEventListener("DOMContentLoaded", function() {
    const chatInput = document.getElementById("chat");
    const sendButton = document.getElementById("send");

    if (!(chatInput && sendButton)) {
        // This can happen if any of these elements' ids change, or if they are
        // removed.
        // eslint-disable-next-line no-console
        console.error(
            "Chat elements could not be found, skipping common features."
        );

        return;
    }

    // Hit Ctrl / Cmd + Enter to send message while typing.
    chatInput.addEventListener("keydown", function(e) {
        const modifier = e.ctrlKey || e.metaKey;

        if (modifier && e.key === 'Enter') {
            sendButton.click();
        }
    });
});

function isEmpty(message) {
    return message.trim().length === 0;
}
