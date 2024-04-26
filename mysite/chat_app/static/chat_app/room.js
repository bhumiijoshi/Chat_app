const roomName = JSON.parse(document.getElementById("room-name").textContent);
let chat_log = document.querySelector("#chat-log");
let onlineUsersSelector = document.querySelector("#onlineUsersSelector");
let chatMessageInput = document.querySelector("#chat-message-input");

// Routing to websocket for a particular room name
const chatSocket = new WebSocket(
  "ws://" + window.location.host + "/ws/chat/" + roomName + "/"
);

// Getting the name of the target user to send personal message by selecting user name from currently online user list 
onlineUsersSelector.onchange = function() {
    chatMessageInput.value = "/pm " + onlineUsersSelector.value + " ";
    onlineUsersSelector.value = null;
    chatMessageInput.focus();
};

// Function to add an option in online user list
function onlineUsersSelectorAdd(value) {
    if (document.querySelector("option[value='" + value + "']")) return;
    let newOption = document.createElement("option");
    newOption.value = value;
    newOption.innerHTML = value;
    onlineUsersSelector.appendChild(newOption);
}

// Function to removes an option from online user list
function onlineUsersSelectorRemove(value) {
    let oldOption = document.querySelector("option[value='" + value + "']");
    if (oldOption !== null) oldOption.remove();
}

// Receive message from websocket
chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);

  // Handling data according to its type 
  switch (data.type) {
    case "chat_message":
      chat_log.value += data.user + " : " + data.message + "\n";
      break;

    case "user_list":
      for (let i = 0; i < data.users.length; i++) {
        onlineUsersSelectorAdd(data.users[i]);
      }
      break;

    case "user_join":
      chat_log.value += data.user + " joined the room.\n";
      onlineUsersSelectorAdd(data.user);
      break;

    case "user_leave":
      chat_log.value += data.user + " left the room.\n";
      onlineUsersSelectorRemove(data.user);
      break;

    case "private_message":
        chat_log.value += "PM from " + data.user + ": " + data.message + "\n";
        break;
    case "private_message_delivered":
        chat_log.value += "PM to " + data.target + ": " + data.message + "\n";
        break;

    default:
      console.error("Unknown message type!");
      break;
  }

};

// Getting error from websocket
chatSocket.onerror = function (err) {
  console.log("WebSocket encountered an error: " + err.message);
  console.log("Closing the socket.");
  chatSocket.close();
};

// Websocket connection get closed
chatSocket.onclose = function (e) {
  console.error("Chat socket closed unexpectedly");
};


document.querySelector("#chat-message-input").focus();
document.querySelector("#chat-message-input").onkeyup = function (e) {
  if (e.keyCode === 13) {
    // enter, return
    document.querySelector("#chat-message-submit").click();
  }
};

// Sending message to websocket
document.querySelector("#chat-message-submit").onclick = function (e) {
  const messageInputDom = document.querySelector("#chat-message-input");
  const message = messageInputDom.value;
  chatSocket.send(
    JSON.stringify({
      message: message,
    })
  );
  messageInputDom.value = "";
};
