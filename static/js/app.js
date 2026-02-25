// Pilly Cloud - Frontend JavaScript

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

function showToast(message, type = 'info') {
    // Simple toast notification (you can enhance this)
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#34C759' : type === 'error' ? '#FF3B30' : '#007AFF'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// API Functions
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('Error conectando con el servidor', 'error');
        throw error;
    }
}

function formatStatus(status) {
    if (!status) return 'desconocido';
    const s = String(status).toLowerCase();
    const map = {
        'online': 'en línea',
        'offline': 'fuera de línea',
        'pending': 'pendiente',
        'blocked': 'bloqueado'
    };
    return map[s] || status;
}

function formatSeverity(sev) {
    if (!sev) return 'info';
    const s = String(sev).toLowerCase();
    const map = { 'error': 'error', 'warning': 'advertencia', 'info': 'info', 'success': 'ok' };
    return map[s] || sev;
}

// Dashboard Functions
async function loadDashboardStats() {
    try {
        const stats = await fetchAPI('/api/dashboard/stats');

        document.getElementById('total-devices').textContent = stats.total_devices;
        document.getElementById('online-devices').textContent = stats.online_devices;
        document.getElementById('offline-devices').textContent = stats.offline_devices;
        document.getElementById('total-releases').textContent = stats.total_releases;
        document.getElementById('recent-alarms').textContent = stats.recent_alarms;
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

async function loadRecentDevices() {
    try {
        const devices = await fetchAPI('/api/devices/list');
        const tbody = document.getElementById('recent-devices-tbody');

        if (!tbody) return;

        tbody.innerHTML = '';

        const recentDevices = devices.slice(0, 5);

        if (recentDevices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Todavía no hay pastilleros registrados</td></tr>';
            return;
        }

        recentDevices.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${device.device_name || 'Pastillero sin nombre'}</strong><br>
                    <small style="color: var(--gray-500)">${device.mac_address}</small>
                </td>
                <td>${device.ip_address || 'N/A'}</td>
                <td>${device.firmware_version || 'Desconocido'}</td>
                <td>
                    <span class="status-badge status-${device.status}">
                        <span class="status-dot"></span>
                        ${formatStatus(device.status)}
                    </span>
                </td>
                <td>${formatDate(device.last_seen)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading recent devices:', error);
    }
}

// Devices Functions
async function loadDevices() {   // ✅ FIX: antes decía "async async function"
    try {
        const devices = await fetchAPI('/api/devices/list');
        const tbody = document.getElementById('devices-tbody');

        if (!tbody) return;

        tbody.innerHTML = '';

        if (devices.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center">
                        <div class="empty-state">
                            <div class="empty-state-title">No hay pastilleros todavía</div>
                            <div class="empty-state-text">Van a aparecer acá cuando se conecten al sistema</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        devices.forEach(device => {
            const row = document.createElement('tr');
            const maskedKey = device.api_key ? (device.api_key.slice(0, 6) + '…' + device.api_key.slice(-4)) : '—';
            row.innerHTML = `
                <td>
                    <strong>${device.device_name || 'Pastillero sin nombre'}</strong><br>
                    <small style="color: var(--gray-500)">${device.mac_address}</small>
                </td>
                <td>${device.ip_address || 'N/A'}</td>
                <td>${device.ssid || 'N/A'}</td>
                <td>${device.firmware_version || 'Desconocido'}</td>
                <td>
                    <span class="status-badge status-${device.status}">
                        <span class="status-dot"></span>
                        ${formatStatus(device.status)}
                    </span>
                </td>
                <td>${formatUptime(device.uptime || 0)}</td>
                <td>${formatBytes(device.free_heap || 0)}</td>
                <td>${formatDate(device.last_seen)}</td>
                <td>
                    <div class="flex gap-1" style="flex-wrap: wrap;">
                        <button class="btn btn-secondary btn-xs" onclick="copyApiKey('${device.api_key || ''}')">API key</button>
                        <button class="btn btn-secondary btn-xs" onclick="queueRestart(${device.id})">Reiniciar</button>
                        <button class="btn btn-secondary btn-xs" onclick="toggleOTA(${device.id}, ${device.ota_enabled ? 1 : 0})">${device.ota_enabled ? 'OTA: ON' : 'OTA: OFF'}</button>
                        <button class="btn btn-danger btn-xs" onclick="setDeviceState(${device.id}, '${device.admin_state || 'active'}')">${device.admin_state === 'blocked' ? 'Desbloquear' : (device.admin_state === 'suspended' ? 'Activar' : 'Bloquear')}</button>
                        <button class="btn btn-secondary btn-xs" onclick="setTargetFirmware(${device.id})">OTA objetivo</button>
                        <button onclick="deleteDevice(${device.id})" class="btn btn-danger btn-xs">Eliminar</button>
                    </div>
                    <small style="color: var(--gray-500); display:block; margin-top:4px;">${maskedKey}</small>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Releases Functions
async function loadReleases() {
    try {
        const releases = await fetchAPI('/api/releases/list');
        const tbody = document.getElementById('releases-tbody');

        if (!tbody) return;

        tbody.innerHTML = '';

        if (releases.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">
                        <div class="empty-state">
                            <div class="empty-state-title">No firmware releases yet</div>
                            <div class="empty-state-text">Upload your first firmware to get started</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        releases.forEach(release => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${release.version}</strong></td>
                <td>${release.description || 'No description'}</td>
                <td>${release.filename}</td>
                <td>${formatBytes(release.file_size)}</td>
                <td>${formatDate(release.uploaded_at)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteRelease(${release.id}, '${release.version}')">
                        Delete
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading releases:', error);
    }
}

function showUploadModal() {
    document.getElementById('upload-modal')?.classList.add('active');
}

function closeUploadModal() {
    document.getElementById('upload-modal')?.classList.remove('active');
    document.getElementById('upload-form')?.reset();
}

async function uploadRelease(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Uploading...';

    try {
        const response = await fetch('/api/releases/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showToast('Firmware uploaded successfully', 'success');
            closeUploadModal();
            loadReleases();
        } else {
            showToast(result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        showToast('Error uploading firmware', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

async function deleteRelease(id, version) {
    if (!confirm(`Are you sure you want to delete version ${version}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/releases/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Firmware eliminado ✅', 'success');
            loadReleases();
        } else {
            showToast('Error eliminando firmware', 'error');
        }
    } catch (error) {
        showToast('Error eliminando firmware', 'error');
    }
}

async function deleteDevice(deviceId) {
    if (!confirm("¿Seguro que querés eliminar este Pilly?")) return;

    try {
        const response = await fetch(`/api/devices/${deviceId}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (data.success) {
            alert("Pilly eliminado correctamente");
            loadDevices();
        } else {
            alert("Error al eliminar");
        }
    } catch (err) {
        alert("Error de conexión");
    }
}

// Alarms Functions
async function loadAlarms() {
    try {
        const alarms = await fetchAPI('/api/alarms/list');
        const tbody = document.getElementById('alarms-tbody');

        if (!tbody) return;

        tbody.innerHTML = '';

        if (alarms.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">
                        <div class="empty-state">
                            <div class="empty-state-title">Todavía no hay eventos</div>
                            <div class="empty-state-text">Los eventos de tomas/alertas van a aparecer acá</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        alarms.forEach(alarm => {
            const row = document.createElement('tr');
            const severityClass = alarm.severity === 'error' ? 'status-offline' :
                                 alarm.severity === 'warning' ? 'status-warning' :
                                 'status-online';

            row.innerHTML = `
                <td>${formatDate(alarm.created_at)}</td>
                <td>
                    ${alarm.device_name || 'Desconocido Device'}<br>
                    <small style="color: var(--gray-500)">${alarm.mac_address || 'N/A'}</small>
                </td>
                <td>${alarm.alarm_type}</td>
                <td>
                    <span class="status-badge ${severityClass}">
                        <span class="status-dot"></span>
                        ${formatSeverity(alarm.severity)}
                    </span>
                </td>
                <td>${alarm.message}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading alarms:', error);
    }
}

// Auto-refresh functionality
function startAutoRefresh(interval = 30000) {
    const currentPage = window.location.pathname;

    setInterval(() => {
        if (currentPage === '/' || currentPage.includes('dashboard')) {
            loadDashboardStats();
            loadRecentDevices();
        } else if (currentPage.includes('devices')) {
            loadDevices();
        } else if (currentPage.includes('alarms')) {
            loadAlarms();
        }
    }, interval);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = window.location.pathname;

    if (currentPage === '/' || currentPage.includes('dashboard')) {
        loadDashboardStats();
        loadRecentDevices();
        startAutoRefresh();
    } else if (currentPage.includes('devices')) {
        loadDevices();
        startAutoRefresh();
    } else if (currentPage.includes('releases')) {
        loadReleases();
    } else if (currentPage.includes('alarms')) {
        loadAlarms();
        startAutoRefresh();
    }
});

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('upload-modal');
    if (event.target === modal) {
        closeUploadModal();
    }
}

// Device Actions (Admin)
async function copyApiKey(apiKey) {
    if (!apiKey) {
        showToast('Este pastillero todavía no tiene API key', 'error');
        return;
    }
    try {
        await navigator.clipboard.writeText(apiKey);
        showToast('API key copiada ✅', 'success');
    } catch (e) {
        prompt('Copiá la API key:', apiKey);
    }
}

async function setDeviceState(deviceId, currentState) {
    const next = prompt('Estado del pastillero (active | suspended | blocked):', currentState || 'active');
    if (!next) return;
    const state = next.trim().toLowerCase();
    if (!['active','suspended','blocked'].includes(state)) {
        showToast('Estado inválido', 'error');
        return;
    }
    try {
        await fetchAPI(`/api/devices/${deviceId}/set_state`, {
            method: 'POST',
            body: JSON.stringify({ state })
        });
        showToast('Estado actualizado', 'success');
        loadDevices();
    } catch (e) {}
}

async function toggleOTA(deviceId, currentEnabled) {
    const enable = currentEnabled ? 0 : 1;
    const ok = confirm(enable ? '¿Habilitar OTA para este pastillero?' : '¿Deshabilitar OTA para este pastillero?');
    if (!ok) return;
    try {
        await fetchAPI(`/api/devices/${deviceId}/ota`, {
            method: 'POST',
            body: JSON.stringify({ ota_enabled: enable })
        });
        showToast('OTA actualizado', 'success');
        loadDevices();
    } catch (e) {}
}

async function setTargetFirmware(deviceId) {
    const version = prompt('Versión objetivo (dejá vacío para quitar objetivo):', '');
    if (version === null) return;
    try {
        await fetchAPI(`/api/devices/${deviceId}/ota`, {
            method: 'POST',
            body: JSON.stringify({ ota_target_version: version.trim() })
        });
        showToast('Objetivo OTA actualizado', 'success');
        loadDevices();
    } catch (e) {}
}

async function queueRestart(deviceId) {
    const ok = confirm('¿Reiniciar remotamente este pastillero en el próximo heartbeat?');
    if (!ok) return;
    try {
        await fetchAPI(`/api/devices/${deviceId}/command`, {
            method: 'POST',
            body: JSON.stringify({ command: 'restart' })
        });
        showToast('Reinicio en cola ✅', 'success');
    } catch (e) {}
}

// ---- Device provisioning (create from panel) ----
function openAddDeviceModal() {
    const modal = document.getElementById('add-device-modal');
    const form = document.getElementById('add-device-form');
    const result = document.getElementById('add-device-result');
    if (form) form.reset();
    if (result) result.style.display = 'none';
    if (modal) modal.classList.add('active');
}

function closeAddDeviceModal() {
    const modal = document.getElementById('add-device-modal');
    if (modal) modal.classList.remove('active');
}

async function createDeviceFromPanel(event) {
    event.preventDefault();

    const mac = document.getElementById('add-mac')?.value?.trim();
    const name = document.getElementById('add-name')?.value?.trim();
    const fw = document.getElementById('add-fw')?.value?.trim();
    const state = document.getElementById('add-state')?.value || 'active';
    const otaEnabled = document.getElementById('add-ota')?.checked ? 1 : 0;
    const target = document.getElementById('add-target')?.value?.trim();

    if (!mac) {
        alert('MAC requerida');
        return;
    }

    try {
        const res = await fetchAPI('/api/devices', {
            method: 'POST',
            body: JSON.stringify({
                mac_address: mac,
                device_name: name,
                firmware_version: fw,
                admin_state: state,
                ota_enabled: otaEnabled,
                ota_target_version: target
            })
        });

        const result = document.getElementById('add-device-result');
        const keyInput = document.getElementById('add-api-key');
        if (keyInput) keyInput.value = res.api_key || '';
        if (result) result.style.display = 'block';

        // refresh table
        await loadDevices();
    } catch (err) {
        console.error(err);
        alert('No pude crear el pastillero. Revisá la MAC y que no exista ya.');
    }
}

function copyProvisionKey() {
    const keyInput = document.getElementById('add-api-key');
    if (!keyInput) return;
    keyInput.select();
    keyInput.setSelectionRange(0, 99999);
    document.execCommand('copy');
}