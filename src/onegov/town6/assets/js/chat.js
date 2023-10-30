document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;


    console.log(endpoint)
    console.log(schema)

    function onWebsocketNotification(message, _websocket) {
        console.log('Ich ha öpis becho!')
        console.log(message)
        console.log(message.text)
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    if (endpoint && schema) {
        const websocket = openWebsocket(
            endpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError
        );

        // Send text to websocket
        $("#chat-form").submit(function(e) {
            e.preventDefault();
            console.log('Dröckt escher')

            const XHR = new XMLHttpRequest();
          
            const urlEncodedDataPairs = [];
          
            // Turn the data object into an array of URL-encoded key/value pairs.
            for (const [name, value] of Object.entries(data)) {
              urlEncodedDataPairs.push(
                `${encodeURIComponent(name)}=${encodeURIComponent(value)}`,
              );
            }
          
            // Combine the pairs into a single string and replace all %-encoded spaces to
            // the '+' character; matches the behavior of browser form submissions.
            const urlEncodedData = urlEncodedDataPairs.join("&").replace(/%20/g, "+");
          
            // Define what happens on successful data submission
            XHR.addEventListener("load", (event) => {
              alert("Yeah! Data sent and response loaded.");
            });
          
            // Define what happens in case of an error
            XHR.addEventListener("error", (event) => {
              alert("Oops! Something went wrong.");
            });
          
            // Set up our request
            XHR.open("POST", "/onegov_town6/meggen/chats");
          
            // Add the required HTTP header for form data POST requests
            XHR.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
          
            // Finally, send our data.
            XHR.send(urlEncodedData);
        });

    }

});
