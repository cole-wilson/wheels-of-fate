clippy.BASE_PATH = "./clippy/agents/"

agent = null;

sounds = {
	welcome: new Howl({src: ['sounds/welcome.m4a']}),
	1: new Howl({src: ['sounds/1.m4a']}),
	2: new Howl({src: ['sounds/2.m4a']}),
	3: new Howl({src: ['sounds/3.m4a']}),
	4: new Howl({src: ['sounds/4.m4a']}),
	5: new Howl({src: ['sounds/5.m4a']}),
	6: new Howl({src: ['sounds/6.m4a']}),
	roll: [new Howl({src: ['sounds/roll1.m4a']}),new Howl({src: ['sounds/roll2.m4a']}),new Howl({src: ['sounds/roll3.m4a']}),new Howl({src: ['sounds/roll4.m4a']})],
	roll_extra: new Howl({src: ['sounds/roll_extra.m4a']}),
};

function lightning(t=2000) {
	let l = document.getElementById("light");
	l.style.display = "block";
	setTimeout((_)=>{l.style.display = "none";}, t)
}

function load() {
	sounds.welcome.play();
	document.getElementById("loadbutton").remove();
	setTimeout(()=>{
	let doors = document.getElementById("load");
	doors.src = "./doors.gif";

	setTimeout((_)=>{
			doors.style.opacity = 0;
			setTimeout((_)=>{doors.style.visibility="hidden"}, 1000);
		// doors.remove();
		//
			setTimeout(lightning, 3700);
			setTimeout((_)=>{
			clippy.load('Merlin', function(agent) {
				agent.moveTo(230,190);
				agent.show();
				agent.speak("Welcome to Wheels of Fate!...");
				window.agent = agent;
			});
			document.getElementById("cam").style.opacity = 1;
			},3000);
		}, 3000);
	}, 2000);
}

ws = new WebSocket("ws://"+location.hostname+":9191")
ws.onmessage = d => {
	let probs = JSON.parse(d.data);

	if (probs === true) {
		roll();
		return;
	}

	console.log(probs);

	let xs = [];
	var n_dice = getdice2().length;
	var is_advdis = false;
	if (!document.getElementById("normal").checked) {
		n_dice = 1;
		is_advdis = true;
	}
	var sum = 0;
	for (var i=0;i<(probs.length);i++) {
		xs.push(n_dice+i);
		sum += (n_dice+i) * probs[i];
	}

	let config = {x:xs, y:probs, type:'bar',marker: {color: '#222'},};
	console.log(config);

	Plotly.newPlot('chart', [config], {
		height: 200,
		margin:{l:60,r:0,t:30,b:40},
		paper_bgcolor:"transparent",
		plot_bgcolor:"transparent",
		title: {text:"Roll "+(is_advdis?"Outcome":"Sum")+" Probability Distribution",font:{family:"frost-scream"}},
		xaxis: {
				title: {
				text: "Roll " + (is_advdis?"Outcome":"Sum"),
				font: {family:"frost-scream"}
			}
		},
		yaxis: {
			title: {
				text: "Probability",
				font: {family:"frost-scream"}
			}
		}
	});
	document.getElementById("avg").innerText = "Average: " + Math.round(sum*1000)/1000;

};

function getdice2() {
	var dice = {
		4: document.getElementById("d4").value,
		6: document.getElementById("d6").value,
		8: document.getElementById("d8").value,
		10: document.getElementById("d10").value,
		12: document.getElementById("d12").value,
		20: document.getElementById("d20").value,
	};

	var dice2 = [];

	Object.keys(dice).forEach(k=>{
		for (var i=0;i<dice[k];i++) {
			dice2.push(parseInt(k));
		}
	});
	return dice2;
}

function convolve(e) {
	document.getElementById("normal").checked = true;
	ws.send(JSON.stringify({type:"convolve",dice:getdice2()}))
}

function playchange(e) {
	sounds[e.value].play();
}

function roll() {
	var is_extra = Math.random() > 0.9;
	var s;
	if (is_extra) {s = sounds.roll_extra;}
	else {
		s = sounds.roll[Math.floor(Math.random()*4)];
	}
	lightning(s.duration()*1000);
	s.play();
	ws.send(JSON.stringify({type:"roll",dice:getdice2()}))
}
function set2_20() {
	[4,6,8,10,12,20].forEach(d=>{
		let e = document.getElementById("d"+d);
		if (d == 20) e.value = 2;
		else e.value = 0;
	})
}

function adv() {
	set2_20();
	ws.send(JSON.stringify({type:"advantage",dice:getdice2()}))
}
function dis() {
	set2_20();
	ws.send(JSON.stringify({type:"disadvantage",dice:getdice2()}))
}

// setTimeout(convolve, 1000);
