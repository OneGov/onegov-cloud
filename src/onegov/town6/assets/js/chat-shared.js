/**
 * Common features shared between staff and client chat.
 */
document.addEventListener("DOMContentLoaded", function() {
    const chatInput = document.getElementById("chat");
    const sendButton = document.getElementById("send");

    if (!(chatInput && sendButton)) {
        // This can happen if any of these elements' ids change, or if they are
        // removed.
        console.error(
            "Chat elements could not be found, skipping common features."
        )

        return;
    }

    // Hit Shift + Enter to send message while typing.
    chatInput.addEventListener("keydown", function(e) {
        if (e.shiftKey && e.key === 'Enter') {
            sendButton.click();
        }
    });
});