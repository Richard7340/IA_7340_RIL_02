import React from 'react';
import axios from 'axios';

export default function ControlPanel() {
  const [controlTotal, setControlTotal] = React.useState(false);
  const [status, setStatus] = React.useState('');
  const [habilidades, setHabilidades] = React.useState({});

  React.useEffect(() => {
    axios.get('http://localhost:5000/estado-control-total').then(r => setControlTotal(r.data.control_total));
    axios.post('http://localhost:5000/conversar', { mensaje: 'leerjson' }).then(r => {
      try {
        const json = JSON.parse(r.data.respuesta.replace(/^.*?\n/, ''));
        setHabilidades(json.habilidades || {});
      } catch {}
    });
  }, []);

  const toggleControl = () => {
    const endpoint = controlTotal ? '/desactivar-control-total' : '/activar-control-total';
    axios.post(`http://localhost:5000${endpoint}`)
      .then(() => {
        setControlTotal(!controlTotal);
        setStatus(controlTotal ? '🔒 Control desactivado' : '🔓 Control activado');
      })
      .catch(() => setStatus('❌ Error en modo control'));
  };

  const quickAction = cmd => async () => {
    try {
      const res = await axios.post('http://localhost:5000/conversar', { mensaje: cmd });
      setStatus(`Acción ejecutada: ${res.data.respuesta}`);
    } catch (err) {
      setStatus('❌ Error al ejecutar acción rápida');
    }
  };

  return (
    <aside className="sidebar">
      <h2>Asistente IA</h2>
      <button onClick={toggleControl} className={controlTotal ? 'btn-danger' : 'btn-success'}>
        {controlTotal ? 'Desactivar Control' : 'Activar Control'}
      </button>
      <div className="status">{status}</div>

      <section>
        <h3>Habilidades</h3>
        <ul>
          {Object.entries(habilidades).map(([k, v]) => <li key={k}>{k}: {v}</li>)}
        </ul>
      </section>

      <section>
        <h3>Acciones Rápidas</h3>
        <button onClick={quickAction('listar archivos')}>📂 Listar archivos</button>
        <button onClick={quickAction('leerjson')}>📖 Leer conciencia</button>
        <button onClick={quickAction('descargar https://python.org/python.exe')}>⬇️ Descargar Python</button>
        <button onClick={quickAction('escanear sistema')}>🛰 Escanear sistema</button>
      </section>
    </aside>
  );
}
