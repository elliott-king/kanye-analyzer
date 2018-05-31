// const WebSocket = require('ws');
var port = 8080;
// var port = 443;
var ws = new WebSocket("ws://localhost:" + port);
// var ws = new WebSocket("wss://cannibaltaylor.com");
ws.onopen = function() {
	console.log("Connected");
}

divQueue = []
// queues in js: https://stackoverflow.com/questions/1590247/how-do-you-implement-a-stack-and-a-queue-in-javascript#1590262

function createDiv(comment) {
	// https://stackoverflow.com/questions/6840326/how-can-i-create-and-style-a-div-using-javascript
        var div = document.createElement("DIV");
        var fullname = comment.data.name;
        div.id = fullname;
        div.className = "individual-res";

	var user = document.createElement("P");
        user.className = "res-user";
        user.appendChild(document.createTextNode(comment.data.author));
        div.appendChild(user);

    var datePosted = document.createElement("P");
        datePosted.className = "res-date";
        datePosted.appendChild(document.createTextNode(new Date()));
        div.appendChild(datePosted);

	var commentBody = document.createElement("P");
        commentBody.className = "res-comment";
        commentBody.appendChild(document.createTextNode(comment.data.body));
        div.appendChild(commentBody);
    return div;
}

function addComment(comment) {
	// First remove from queue & DOM if already five comments.

	console.log("Comment posted by: " + comment.data.author);
	console.log("Contents: " + comment.data.body);

    if (divQueue.length === 5) {
		var oldestCommentFullname = divQueue.shift();
		var oldestCommentDiv = document.getElementById(oldestCommentFullname);
		oldestCommentDiv.parentNode.removeChild(oldestCommentDiv);
	}

	// Add to queue and DOM.
	var newCommentDiv = createDiv(comment);
	var fullname = comment.data.name;
	divQueue.push(fullname);

	var containerDiv = document.getElementById("realtime-container");
    console.log(containerDiv);
	containerDiv.appendChild(newCommentDiv);

}
ws.onmessage = function(comment) {
	addComment(JSON.parse(comment.data));
};

ws.onclose = function() {
	console.log("Disconnected");
};