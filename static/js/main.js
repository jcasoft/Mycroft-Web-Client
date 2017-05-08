$(document).ready(function(){

var received = $('#received');


var socket = new WebSocket("ws://localhost:8181/ws");
 
socket.onopen = function(){  
  console.log("connected"); 
}; 

socket.onmessage = function (message) {
  console.log("receiving: " + message.data);
  received.append(message.data);

  var msg = message.data.substr(0, 1);
  if (msg == "-")
  {
	// received.append($("#received").css({"color": "#3498D8"}));
	received.append($("#received").css({"color": "#666666"}));
	received.append($('<br/>'));
  } else {
	// received.append($("#received").css({"color": "#35495d"}));
	received.append($("#received").css({"color": "#999999"}));
	received.append($('<br/>'));
  }

  $("#received").scrollTop($("#received")[0].scrollHeight);

};

socket.onclose = function(){
  console.log("disconnected"); 
};

var sendMessage = function(message) {
  console.log("sending:" + message.data);
  socket.send(message.data);
};



$("#cmd_send").click(function(ev){
  ev.preventDefault();
  var cmd = $('#cmd_value').val();
  sendMessage({ 'data' : cmd});
  $('#cmd_value').val("");
});

$('#clear').click(function(){
  received.empty();
});

$('#stop').click(function(){
   sendMessage({ 'data' : 'stop'});
});

});
