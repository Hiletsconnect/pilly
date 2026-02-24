async function api(path, opts={}) {
  const res = await fetch(path, opts);
  if (!res.ok) throw await res.json().catch(()=>({detail:"Error"}));
  return res.json();
}

const devicesList = document.getElementById("devicesList");
const deviceSelect = document.getElementById("deviceSelect");
const scheduleJson = document.getElementById("scheduleJson");
const msg = document.getElementById("msg");

async function loadDevices(){
  const j = await api("/api/devices");
  devicesList.innerHTML = "";
  deviceSelect.innerHTML = "";

  j.devices.forEach(d => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
        <div>
          <div style="font-weight:700">${d.name} <span class="badge ${d.online?'ok':'no'}">${d.online?'online':'offline'}</span></div>
          <div class="muted" style="font-size:13px">MAC: ${d.mac} · IP: ${d.ip||'-'} · WiFi: ${d.ssid||'-'} · FW: ${d.fw_version||'-'}</div>
        </div>
      </div>
    `;
    devicesList.appendChild(el);

    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `${d.name} (${d.mac})`;
    deviceSelect.appendChild(opt);
  });

  if (j.devices.length === 0){
    devicesList.innerHTML = `<div class="item"><div class="muted">No tenés dispositivos cargados todavía.</div></div>`;
  }
}

document.getElementById("loadSchedule").addEventListener("click", async ()=>{
  msg.textContent = "";
  const id = deviceSelect.value;
  const j = await api(`/api/devices/${id}/schedule`);
  scheduleJson.value = JSON.stringify(j.payload, null, 2);
});

document.getElementById("saveSchedule").addEventListener("click", async ()=>{
  msg.textContent = "";
  const id = deviceSelect.value;
  let payload;
  try{
    payload = JSON.parse(scheduleJson.value || "{}");
  }catch(e){
    msg.textContent = "JSON inválido.";
    return;
  }
  await api(`/api/devices/${id}/schedule`, {
    method:"PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({payload})
  });
  msg.textContent = "Guardado y enviado por MQTT.";
});

document.getElementById("testBtn").addEventListener("click", async ()=>{
  msg.textContent = "";
  const id = deviceSelect.value;
  const slot = parseInt(document.getElementById("slot").value,10);
  const color = document.getElementById("color").value;
  const duration_sec = parseInt(document.getElementById("dur").value,10);
  await api(`/api/devices/${id}/test/slot`, {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({slot, color, duration_sec})
  });
  msg.textContent = "Comando test enviado.";
});

document.getElementById("logoutBtn").addEventListener("click", async ()=>{
  await fetch("/api/auth/logout", {method:"POST"});
  window.location.href = "/login";
});

loadDevices().catch(()=>{});