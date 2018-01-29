var data = {
	loaded: false,
	devices: [],
};

function getDevices(){
	var req = new XMLHttpRequest();
	req.onreadystatechange = function(){
		if(req.readyState === XMLHttpRequest.DONE){
			if(req.status == 200){
				console.log("Incoming data.");
				console.log(req.responseText);
				while(data.length > 1){
					data.devices.pop();
				}
				data.loaded = true;
				data.devices = JSON.parse(req.responseText);
			} else {
				console.log("Error.");
			}
		}
	};

	req.open('GET', '/devices', true);
	req.send();
}

function getBrowsers(){
	alert("On the TODO");
}

function launch(id, browser){
	if(!browser){
		browser = "Chrome";
	}
	var req = new XMLHttpRequest();
	req.onreadystatechange = function(){
		if(req.readyState === XMLHttpRequest.DONE){
			if(req.status == 200){
				console.log("Incoming data.");
				alert(req.responseText);
			} else {
				console.log("Error.");
			}
		}
	}

	req.open('GET', '/launchadb/' + id + '/' + browser, true);
	req.send();
}

Vue.component('dev-listing', {
	props: ['device'],
	template:'<li>{{device.name}}&nbsp;' +
		'<button v-bind:id="device.name" onclick="location.href=\'/begin/\'+this.id;">Browser</button>' +
		'<button v-bind:id="device.name" onclick="launch(this.id)">ADB</button>' +
		'</li>'
});

Vue.component('devicemenu', {
	props: ['ready', 'devices'],
	template: `<div>
		<p v-if="!ready">Loading</p>
		<ol>
			<dev-listing v-if="ready" v-for="dev in devices" v-bind:key="dev.name"
				v-bind:device="dev"/>
		</ol>
	</div>`
});

var app = new Vue({
	el: '#panel-app',
	data: data
});

getDevices();

setInterval(function(){
	getDevices();
}, 3000);
