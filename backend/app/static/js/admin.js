async function api(path, opts={}) {
  const res = await fetch(path, opts);
  if (!res.ok) throw await res.json().catch(()=>({detail:"Error"}));
  return res.json();
}

const adminDevices = document.getElementById("adminDevices");
const fwList = document.getElementById("fwList");
const fwMsg = document.getElementById("fwMsg");

async function loadAdminDevices(){
  const j = await api("/api/admin/devices");
  adminDevices.innerHTML = "";
  j.devices.forEach(d => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
        <div>
          <div style="font-weight:700">${d.name} <span class="badge ${d.online?'ok':'no'}">${d.online?'online':'offline'}</span></div>
          <div class="muted" style="font-size:13px">MAC: ${d.mac} · IP: ${d.ip||'-'} · WiFi: ${d.ssid||'-'} · FW: ${d.fw_version||'-'}</div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end">
          <button class="btn ghost" data-reboot="${d.id}">Reboot</button>
        </div>
      </div>
    `;
    adminDevices.appendChild(el);
  });

  adminDevices.querySelectorAll("button[data-reboot]").forEach(btn=>{
    btn.addEventListener("click", async ()=>{
      const id = btn.getAttribute("data-reboot");
      await api(`/api/admin/devices/${id}/cmd/reboot`, {method:"POST"});
      alert("Reboot enviado");
    });
  });
}

async function loadFirmware(){
  const j = await api("/api/admin/firmware");
  fwList.innerHTML = "";
  j.firmware.forEach(f => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
        <div>
          <div style="font-weight:700">${f.version} <span class="badge ok">stable</span></div>
          <div class="muted" style="font-size:13px">id=${f.id} · size=${f.size_bytes} · sha=${(f.sha256||"").slice(0,12)}…</div>
        </div>
      </div>
    `;
    fwList.appendChild(el);
  });
}

document.getElementById("fwForm").addEventListener("submit", async (e)=>{
  e.preventDefault();
  fwMsg.textContent = "";
  const fd = new FormData(e.target);
  const res = await fetch("/api/admin/firmware/upload", {method:"POST", body: fd});
  if(!res.ok){
    const j = await res.json().catch(()=>({detail:"Error"}));
    fwMsg.textContent = j.detail || "Error subiendo";
    return;
  }
  fwMsg.textContent = "Firmware subido.";
  e.target.reset();
  await loadFirmware();
});

document.getElementById("logoutBtn").addEventListener("click", async ()=>{
  await fetch("/api/auth/logout", {method:"POST"});
  window.location.href = "/login";
});

loadAdminDevices().catch(()=>{});
loadFirmware().catch(()=>{});