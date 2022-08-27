// this is for the /chat page

// vars
const chatContent = document.getElementById("chat-content");
// const workspaceID = location.href.split('/').at(-2);

// this function will mark msgs sent by current user to be green
function labelMessage(messageElement, messageSender, message) {
	fetch('/api/v1/email')
  .then(res => res.json())
  .then(data => {
		if (data.email == message.sender) {
			messageElement.classList.add("client-sent");
			messageSender.innerHTML += " (You)";
		}
	});
}

function appendChatMsg(message) {
	const chatMessage = document.createElement('div');
	chatMessage.classList.add("message");

	const messageSender = document.createElement('p');
	messageSender.classList.add('sender');
	messageSender.innerText = message.sender;
	
	labelMessage(chatMessage, messageSender, message);

	const messageContent = document.createElement('pre');
	messageContent.innerText = message.message;

	chatMessage.appendChild(messageSender);
	chatMessage.appendChild(messageContent);

	chatContent.appendChild(chatMessage); // append that message to the chat

	var chatHeight = chatContent.clientHeight;
	var chatScrollHeight = chatContent.scrollHeight;
	var chatScrollPosition = chatContent.scrollTop;
	
	chatContent.scrollTop = chatScrollHeight;
}

// Initiate socket connection
var socket = io();

// On connect
socket.on('connect', function() {
  socket.emit('join', {workspace: workspaceID});
	fetch('/api/v1/chat?id=' + workspaceID)
        .then((response) => response.json())
        .then((data) => {
			for (let i = 0; i < data.length; i++) {
				appendChatMsg(data[i]);
			}
		});
});


// This is what receives a message broadcast from the server
socket.on('message', (data) => {
	appendChatMsg(data);
});


// When user clicks send on  message
const messageForm = document.querySelector("#message-editor form");
const message = document.querySelector("#message-editor form input");

messageForm.addEventListener('submit', (e) => {
	e.preventDefault();

	fetch('/api/v1/email').then((response) => response.json()).then(
		(data) => {
			// Sends the 'message' event
			socket.send({"workspace": workspaceID, "message_data": {"sender": data.email, "message": message.value}});
			message.value = '';
		}
	);
});