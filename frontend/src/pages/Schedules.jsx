import { useState, useEffect } from 'react';
import { schedulesAPI, devicesAPI } from '../services/api';
import { Calendar, Plus, Edit, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Schedules() {
  const [schedules, setSchedules] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [schedulesRes, devicesRes] = await Promise.all([
        schedulesAPI.getAll(),
        devicesAPI.getAll(),
      ]);
      setSchedules(schedulesRes.data);
      setDevices(devicesRes.data);
    } catch (error) {
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Eliminar este horario?')) return;
    try {
      await schedulesAPI.delete(id);
      toast.success('Horario eliminado');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const days = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Horarios de Medicación</h1>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Nuevo Horario
        </button>
      </div>

      <div className="grid gap-4">
        {schedules.map((schedule) => (
          <div key={schedule.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex gap-4 flex-1">
                <div 
                  className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl font-bold text-white shadow-lg"
                  style={{ backgroundColor: schedule.led_color }}
                >
                  {schedule.compartment_number + 1}
                </div>
                
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900">{schedule.medication_name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{schedule.dosage}</p>
                  <p className="text-sm text-gray-500 mt-1">{schedule.instructions}</p>
                  
                  <div className="flex gap-4 mt-3">
                    <div className="text-sm">
                      <span className="text-gray-600">Hora: </span>
                      <span className="font-medium">{schedule.schedule_time}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-gray-600">Días: </span>
                      <span className="font-medium">
                        {schedule.days_of_week.map(d => days[d]).join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button className="btn-secondary p-2">
                  <Edit className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => handleDelete(schedule.id)}
                  className="btn-danger p-2"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
