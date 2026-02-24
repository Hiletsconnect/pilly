import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Activity, 
  Calendar, 
  Pill, 
  Wifi, 
  WifiOff,
  AlertCircle,
  TrendingUp
} from 'lucide-react';
import { devicesAPI, schedulesAPI } from '../services/api';
import { useAuthStore } from '../store/useStore';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export default function Home() {
  const { user } = useAuthStore();
  const [devices, setDevices] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [devicesRes, schedulesRes] = await Promise.all([
        devicesAPI.getAll(),
        schedulesAPI.getAll(),
      ]);
      setDevices(devicesRes.data);
      setSchedules(schedulesRes.data);
    } catch (error) {
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const onlineDevices = devices.filter(d => d.is_online).length;
  const activeSchedules = schedules.filter(s => s.is_active).length;
  const todaySchedules = schedules.filter(s => {
    const today = new Date().getDay();
    return s.is_active && s.days_of_week.includes(today);
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          ¡Bienvenido, {user?.full_name || user?.username}! 👋
        </h1>
        <p className="text-gray-600 mt-2">
          Aquí está el resumen de tu sistema de medicación
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-primary-100 text-sm">Dispositivos Online</p>
              <p className="text-3xl font-bold mt-1">{onlineDevices}/{devices.length}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Wifi className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-accent-500 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Horarios Activos</p>
              <p className="text-3xl font-bold mt-1">{activeSchedules}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Calendar className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-green-500 to-emerald-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Medicamentos Hoy</p>
              <p className="text-3xl font-bold mt-1">{todaySchedules.length}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Pill className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="card bg-gradient-to-br from-orange-500 to-red-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">Próximo en</p>
              <p className="text-3xl font-bold mt-1">2h</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Devices Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Dispositivos</h2>
            <Link to="/dashboard/devices" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              Ver todos →
            </Link>
          </div>
          <div className="space-y-3">
            {devices.slice(0, 3).map((device) => (
              <div key={device.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {device.is_online ? (
                    <Wifi className="w-5 h-5 text-green-500" />
                  ) : (
                    <WifiOff className="w-5 h-5 text-gray-400" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900">{device.name}</p>
                    <p className="text-xs text-gray-500">{device.device_id}</p>
                  </div>
                </div>
                <span className={`badge ${device.is_online ? 'badge-success' : 'badge-danger'}`}>
                  {device.is_online ? 'Online' : 'Offline'}
                </span>
              </div>
            ))}
            {devices.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No hay dispositivos registrados</p>
                <Link to="/dashboard/devices" className="text-primary-600 hover:text-primary-700 text-sm font-medium mt-2 inline-block">
                  Agregar dispositivo
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Today's Schedule */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Horarios de Hoy</h2>
            <Link to="/dashboard/schedules" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              Ver todos →
            </Link>
          </div>
          <div className="space-y-3">
            {todaySchedules.slice(0, 3).map((schedule) => (
              <div key={schedule.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: schedule.led_color }}
                />
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{schedule.medication_name}</p>
                  <p className="text-xs text-gray-500">
                    {schedule.schedule_time} - Compartimento {schedule.compartment_number + 1}
                  </p>
                </div>
              </div>
            ))}
            {todaySchedules.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No hay medicamentos programados para hoy</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
