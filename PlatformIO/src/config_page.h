#pragma once
// Page de configuration servie sur "/". Les échanges passent par le WebSocket "/ws" :
//   page → ESP32 : {"cmd":"get"}, {"cmd":"save",...}, {"cmd":"name","id":..,"name":..},
//                  {"cmd":"scan"}, {"cmd":"moisture"}, {"cmd":"reset"},
//                  {"cmd":"mode","relay":"pump"|"light","mode":"auto"|"moisture"|"on"|"off"} ("moisture" : pompe uniquement)
//   ESP32 → page : {"type":"state",...} (état et réglages), {"type":"result","ok":..,"msg":..}

#include <Arduino.h>

const char SEMX_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SemX</title><style>
:root{--bg:#f4f6f8;--card:#fff;--fg:#1d2733;--mut:#6b7785;--line:#dde3ea;--acc:#1f7a5a;--err:#c0392b}
@media(prefers-color-scheme:dark){:root{--bg:#12171d;--card:#1b232c;--fg:#e6ebf0;--mut:#93a0ad;--line:#2c3742;--acc:#3fbf8f;--err:#ff6b5b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:560px;margin:0 auto;padding:16px}h1{font-size:1.4em;margin:8px 0 4px}
h2{font-size:1.05em;margin:0 0 10px;display:flex;gap:8px;align-items:center}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:0 16px;margin-bottom:14px}
details[open]{padding-bottom:14px}summary{list-style:none;cursor:pointer;padding:14px 0;user-select:none}
summary::-webkit-details-marker{display:none}summary h2{margin:0}
summary h2::before{content:'▸';color:var(--mut);transition:transform .15s}details[open] summary h2::before{transform:rotate(90deg)}
details[open] summary{padding-bottom:10px}
label{display:block;margin:10px 0 4px;font-weight:600}
input{width:100%;padding:9px 10px;margin-top:4px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit}
button{width:100%;margin-top:12px;padding:10px;border:0;border-radius:6px;background:var(--acc);color:#fff;font:inherit;font-weight:600;cursor:pointer}
button.sec{background:transparent;color:var(--acc);border:1px solid var(--line)}button.danger{background:var(--err)}
button:disabled{opacity:.5;cursor:default}
.muted{color:var(--mut);font-size:.9em}.row{display:flex;gap:8px;align-items:flex-end}.row>*{flex:1}
.row button{flex:0 0 auto;width:auto;padding:10px 14px}
.sensor{border-top:1px solid var(--line);padding:8px 0}.sensor:first-of-type{border-top:0}
.val{font-size:1.6em;font-weight:600}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;background:#999}
.dot.on{background:var(--acc)}.dot.err{background:var(--err)}.badge{margin-left:auto;font-size:.8em;font-weight:500;color:var(--mut)}
.seg{display:flex;flex-wrap:wrap;gap:6px}.seg button{flex:1 1 110px;margin-top:8px;padding:8px}
h3{font-size:.95em;margin:16px 0 0}
.forced{color:var(--err);font-weight:600}
#msg{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);width:max-content;max-width:calc(100% - 32px);margin:0;
padding:10px 16px;border-radius:8px;background:var(--acc);color:#fff;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.25)}
#msg:empty{display:none}#msg.err{background:var(--err)}
</style></head><body><main>
<h1>SemX</h1>
<p class="muted"><span id="ws-dot" class="dot"></span><span id="ws-state">Connexion…</span> · Heure : <b id="clock">–</b> · <a href="/status">Statut</a></p>

<details data-k="sensors"><summary><h2>Sondes de température <span class="badge" id="ds-count"></span></h2></summary>
<p class="muted">Une sonde sans nom n'envoie pas ses mesures sur MQTT. Le nom est utilisé dans le topic
« <span class="dev"></span>/temperature/&lt;nom&gt; » (lettres, chiffres, « _ » et « - »).</p>
<div id="sensors"></div>
<button type="button" class="sec" id="scan">Rechercher les sondes</button></details>

<form id="cfg">
<details data-k="measure"><summary><h2>Mesures <span class="badge" id="meas-state"></span></h2></summary>
<div class="row"><label>Intervalle (min)<input type="number" id="meas-m" min="0" max="60"></label>
<label>(s)<input type="number" id="meas-s" min="0" max="59"></label></div>
<p class="muted">De 2 s à 1 h, pour les sondes de température et d'humidité. En mode humidité,
la pompe réagit au plus tard un intervalle après le passage d'un seuil.</p></details>

<details data-k="moisture"><summary><h2>Humidité du sol <span class="badge" id="mo-state"></span></h2></summary>
<p><span class="val" id="mo-pct">–</span> <span class="muted" id="mo-raw"></span></p>
<button type="button" class="sec" id="mo-read">Lire la sonde maintenant</button>
<p class="muted">Calibration : placez la sonde à l'air libre puis dans l'eau, et relevez la valeur brute à chaque fois.</p>
<div class="row"><label>Sec (0 %)<input type="number" id="dry" min="0" max="4095" required></label>
<button type="button" class="sec" data-take="dry">Valeur actuelle</button></div>
<div class="row"><label>Humide (100 %)<input type="number" id="wet" min="0" max="4095" required></label>
<button type="button" class="sec" data-take="wet">Valeur actuelle</button></div></details>

<details data-k="pump"><summary><h2>Pompe <span class="badge"><span id="pump-dot" class="dot"></span><span id="pump-state">–</span></span></h2></summary>
<div class="seg" data-relay="pump"><button type="button" data-mode="auto">Automatique</button>
<button type="button" data-mode="moisture">Humidité</button>
<button type="button" data-mode="on">Marche forcée</button><button type="button" data-mode="off">Arrêt forcé</button></div>
<p class="muted forced" id="pump-forced" hidden>Mode forcé : les réglages ci-dessous sont ignorés.</p>
<p><b id="moist-state"></b></p>
<h3>Mode automatique : cycle</h3>
<div class="row"><label>Marche (h)<input type="number" id="pon-h" min="0" max="24"></label>
<label>(min)<input type="number" id="pon-m" min="0" max="59"></label>
<label>(s)<input type="number" id="pon-s" min="0" max="59"></label></div>
<div class="row"><label>Arrêt (h)<input type="number" id="poff-h" min="0" max="24"></label>
<label>(min)<input type="number" id="poff-m" min="0" max="59"></label>
<label>(s)<input type="number" id="poff-s" min="0" max="59"></label></div>
<p class="muted">De 1 s à 24 h chacune. Le cycle démarre par la période d'arrêt, au démarrage
comme au retour en mode automatique.</p>
<h3>Mode humidité : seuils</h3>
<div class="row"><label>Démarrer sous (%)<input type="number" id="moist-low" min="0" max="99"></label>
<label>Arrêter à (%)<input type="number" id="moist-high" min="1" max="100"></label></div>
<p class="muted">La pompe démarre quand l'humidité passe sous le premier seuil et s'arrête dès que le second
est atteint, sans suivre le cycle. Après un redémarrage, ou en choisissant ce mode, elle démarre si l'humidité
est sous le second seuil. Sans lecture valide de la sonde, la pompe reste arrêtée.</p>
<p class="muted">Le mode choisi (automatique ou humidité) est conservé après un redémarrage, pas les modes forcés.</p></details>

<details data-k="light"><summary><h2>Éclairage <span class="badge"><span id="light-dot" class="dot"></span><span id="light-state">–</span></span></h2></summary>
<div class="seg" data-relay="light"><button type="button" data-mode="auto">Automatique</button>
<button type="button" data-mode="on">Marche forcée</button><button type="button" data-mode="off">Arrêt forcé</button></div>
<p class="muted forced" id="light-forced" hidden>Mode forcé : le réglage automatique ci-dessous est ignoré.</p>
<label>Heure d'allumage<input type="time" id="lstart" required></label>
<div class="row"><label>Durée (h)<input type="number" id="lon-h" min="0" max="24"></label>
<label>(min)<input type="number" id="lon-m" min="0" max="59"></label></div>
<p class="muted" id="lend"></p></details>

<p class="muted">Chaque réglage est enregistré automatiquement dès qu'il est modifié.</p>
<button type="button" class="danger" id="reset">Revenir aux valeurs par défaut</button>
</form>
<p id="msg"></p>
</main><script>
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';');
const pad=n=>String(n).padStart(2,'0');
const num=id=>parseInt($(id).value||'0',10);
let ws,st=null,dirty=false,names={};

function msg(t,err){$('msg').textContent=t;$('msg').className=err?'err':'';clearTimeout(msg.t);if(t&&!err)msg.t=setTimeout(()=>msg(''),3000);}
function send(o){if(ws&&ws.readyState==1){ws.send(JSON.stringify(o));return true;}msg('Non connecté',true);return false;}
function connect(){
  ws=new WebSocket((location.protocol=='https:'?'wss://':'ws://')+location.host+'/ws');
  ws.onopen=()=>{$('ws-dot').className='dot on';$('ws-state').textContent='Connecté';send({cmd:'get'});};
  ws.onclose=()=>{$('ws-dot').className='dot err';$('ws-state').textContent='Déconnecté, reconnexion…';setTimeout(connect,2000);};
  ws.onmessage=e=>{let m;try{m=JSON.parse(e.data);}catch(_){return;}
    if(m.type=='state')show(m);else if(m.type=='result'){msg(m.msg,!m.ok);if(m.ok&&m.reload)dirty=false;}};
}

function show(s){st=s;
  document.querySelectorAll('.dev').forEach(e=>e.textContent=s.device);
  $('clock').textContent=s.time||'non synchronisée';
  const mo=s.moisture;
  $('mo-pct').textContent=mo.valid?mo.percent.toFixed(1)+' %':'–';
  $('mo-raw').textContent='brut '+mo.raw+' · '+mo.mv+' mV';
  $('mo-state').textContent=mo.valid?mo.percent.toFixed(1)+' %':'lecture invalide';
  $('meas-state').textContent='toutes les '+dur(s.cfg.measure);
  for(const k of['pump','light']){$(k+'-dot').className='dot'+(s[k]?' on':'');$(k+'-state').textContent=s[k]?'allumé':'éteint';
    const m=s[k+'Mode'];document.querySelectorAll('[data-relay="'+k+'"] button').forEach(b=>b.className=b.dataset.mode==m?'':'sec');
    $(k+'-forced').hidden=m!='on'&&m!='off';}
  $('moist-state').textContent=s.pumpMode!='moisture'?'':!mo.valid?'Lecture de la sonde invalide : pompe arrêtée.':
    s.soilDry?'Sol sec : arrosage en cours.':'Sol assez humide : en attente.';
  sensors(s.sensors);
  if(!dirty)fill(s.cfg);
}

function sensors(list){
  $('ds-count').textContent=list.length+' détectée'+(list.length>1?'s':'');
  const box=$('sensors');
  if(!list.length){box.innerHTML='<p class="muted">Aucune sonde détectée.</p>';return;}
  const ids=list.map(x=>x.id).join();
  if(box.dataset.ids!=ids){box.dataset.ids=ids;box.innerHTML=list.map(x=>
    '<div class="sensor" data-id="'+esc(x.id)+'"><div class="muted">'+esc(x.id)+' · <b class="t"></b> <span class="mq"></span></div>'+
    '<label>Nom<input class="n" maxlength="32" pattern="[A-Za-z0-9_\\-]*" placeholder="Sans nom : non publiée"></label></div>').join('');
    box.querySelectorAll('.sensor').forEach(d=>{const id=d.dataset.id,inp=d.querySelector('.n');
      inp.oninput=()=>{names[id]=true;};
      inp.onchange=()=>{if(!inp.reportValidity())return;if(send({cmd:'name',id:id,name:inp.value.trim()}))names[id]=false;};});}
  list.forEach(x=>{const d=box.querySelector('[data-id="'+x.id+'"]');
    d.querySelector('.t').textContent=x.valid?x.t.toFixed(2)+' °C':'erreur de lecture';
    d.querySelector('.mq').textContent=x.name?'· publiée':'· non publiée';
    const inp=d.querySelector('.n');if(!names[x.id]&&document.activeElement!=inp)inp.value=x.name;});
}

// Fill the settings fields, except the one being edited
// Duration in seconds as text, e.g. "1 min 30 s"
function dur(t){const h=Math.floor(t/3600),m=Math.floor(t%3600/60),r=t%60;
  return[h&&h+' h',m&&m+' min',r&&r+' s'].filter(Boolean).join(' ')||'0 s';}

function fill(c){
  const set=(id,v)=>{if(document.activeElement!=$(id))$(id).value=v;};
  set('dry',c.dry);set('wet',c.wet);
  set('meas-m',Math.floor(c.measure/60));set('meas-s',c.measure%60);
  set('moist-low',c.moistLow);set('moist-high',c.moistHigh);
  for(const[k,v]of[['pon',c.pumpOn],['poff',c.pumpOff]]){
    set(k+'-h',Math.floor(v/3600));set(k+'-m',Math.floor(v%3600/60));set(k+'-s',v%60);}
  set('lstart',pad(Math.floor(c.lightStart/60))+':'+pad(c.lightStart%60));
  set('lon-h',Math.floor(c.lightOn/60));set('lon-m',c.lightOn%60);
  end();
}

function end(){const[h,m]=($('lstart').value||'0:0').split(':').map(Number),d=num('lon-h')*60+num('lon-m');
  const e=(h*60+m+d)%1440;
  $('lend').textContent=d==0?'Éclairage toujours éteint.':d>=1440?'Éclairage toujours allumé.':'Extinction à '+pad(Math.floor(e/60))+':'+pad(e%60)+'.';}

$('cfg').oninput=()=>{dirty=true;end();};
document.querySelectorAll('[data-take]').forEach(b=>b.onclick=()=>{if(!st)return;$(b.dataset.take).value=st.moisture.raw;dirty=true;save();});
document.querySelectorAll('[data-relay] button').forEach(b=>b.onclick=()=>send({cmd:'mode',relay:b.parentNode.dataset.relay,mode:b.dataset.mode}));
$('mo-read').onclick=()=>send({cmd:'moisture'});
$('scan').onclick=()=>send({cmd:'scan'});
$('reset').onclick=()=>{if(confirm('Revenir aux valeurs par défaut pour la pompe, l\'éclairage et la calibration ?')&&send({cmd:'reset'}))dirty=false;};
// Every change is saved at once. The ESP32 checks all the values together: if they are refused,
// the fields keep what was typed and the error stays displayed until the next successful save.
$('cfg').onsubmit=e=>e.preventDefault();
$('cfg').onchange=e=>{if(e.target.matches('input'))save();};
function save(){
  const[h,m]=$('lstart').value.split(':').map(Number);
  const c={cmd:'save',measure:num('meas-m')*60+num('meas-s'),dry:num('dry'),wet:num('wet'),
    pumpOn:num('pon-h')*3600+num('pon-m')*60+num('pon-s'),pumpOff:num('poff-h')*3600+num('poff-m')*60+num('poff-s'),
    moistLow:num('moist-low'),moistHigh:num('moist-high'),
    lightStart:h*60+m,lightOn:num('lon-h')*60+num('lon-m')};
  if(c.lightOn>1440){msg('Durée d\'allumage : 24 h maximum',true);return;}
  send(c);}
// Cards are folded by default; the cards opened by this viewer are remembered in the browser
document.querySelectorAll('details[data-k]').forEach(d=>{
  try{d.open=localStorage.getItem('open-'+d.dataset.k)=='1';}catch(_){}
  d.ontoggle=()=>{try{localStorage.setItem('open-'+d.dataset.k,d.open?'1':'0');}catch(_){}};});
// Enter confirms a field in every browser: leaving the field fires the change event that saves it
document.addEventListener('keydown',e=>{if(e.key=='Enter'&&e.target.matches('input')){e.preventDefault();e.target.blur();}});
connect();
</script></body></html>)rawliteral";
