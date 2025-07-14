import React from "react";
import axios from "axios";

const ControlPanel = () => {
  const ejecutar = async (endpoint) => {
    try {
      const res = await axios.post(`http://localhost:5000/${endpoint}`);
      alert(res.data?.respuesta || "Acción ejecutada");
    } catch {
      alert("Error al ejecutar acción");
    }
  };

  return (
    <div className="control-panel">
      <h3>Panel de Control</h3>
      <button onClick={() => ejecutar("activar-control-total")}>✅ Activar Control Total</button>
      <button onClick={() => ejecutar("desactivar-control-total")}>❌ Desactivar Control Total</button>
      <button onClick={() => ejecutar("escanear-total")}>📡 Escanear Sistema</button>
      <button onClick={() => ejecutar("listar-archivos")}>📂 Listar Archivos</button>
      <button onClick={() => ejecutar("leer-json")}>📖 Leer Conciencia</button>
    </div>
  );
};

export default ControlPanel;
