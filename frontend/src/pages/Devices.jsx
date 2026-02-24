import { useState, useEffect } from 'react';
import { devicesAPI } from '../services/api';
import { Wifi, WifiOff, Plus, Power, RefreshCw, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await devicesAPI.getAll();
      setDevices(response.data);
    } catch (error) {
      toast.error('Error al cargar dispositivos');
    } finally {
      setLoading(false);
    }
  };

  const handleReboot = async (deviceId, deviceName) => {
    if (!confirm(`¿Reiniciar ${deviceName}?`)) return;
    try {
      await devicesAPI.reboot(deviceId);
      toast.success('Comando de reinicio enviado');
    } catch (error) {
      toast.error('Error al enviar comando');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dispositivos</h1>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Agregar Dispositivo
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {devices.map((device) => (
          <div key={device.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900">{device.name}</h3>
                <p className="text-sm text-gray-500">{device.device_id}</p>
              </div>
              <span className={`badge ${device.is_online ? 'badge-success' : 'badge-danger'}`}>
                {device.is_online ? <Wifi className="w-4 h-4 mr-1" /> : <WifiOff className="w-4 h-4 mr-1" />}
                {device.is_online ? 'Online' : 'Offline'}
              </span>
            </div>

            <div className="space-y-2 mb-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">IP:</span>
                <span className="font-medium">{device.ip_address || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">WiFi:</span>
                <span className="font-medium">{device.wifi_ssid || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Firmware:</span>
                <span className="font-medium">{device.firmware_version || 'N/A'}</span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleReboot(device.id, device.name)}
                className="flex-1 btn-secondary text-sm py-2"
                disabled={!device.is_online}
              >
                <Power className="w-4 h-4 mr-1" />
                Reiniciar
              </button>
              <button className="btn-secondary p-2">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
