// src/components/IAWorkAssistant.jsx
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

export default function IAWorkAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [controlTotal, setControlTotal] = useState(false);
  const [status, setStatus] = useState("");
  const [habilidades, setHabilidades] = useState({});
  const [codigoGenerado, setCodigoGenerado] = useState("");
  const [escaneoSistema, setEscaneoSistema] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    verificarEstadoControl();
    cargarConciencia();
    cargarCodigoAutogenerado();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const verificarEstadoControl = async () => {
    try {
      const res = await axios.get("http://localhost:5000/estado-control-total");
      setControlTotal(res.data.control_total);
    } catch {
      setStatus("❌ Error al obtener estado de control total");
    }
  };

  const cargarConciencia = async () => {
    try {
      const res = await axios.post("http://localhost:5000/conversar", { mensaje: "leer json" });
      const texto = res.data.respuesta;
      const json = JSON.parse(texto.split("\n").slice(1).join("\n"));
      setHabilidades(json?.habilidades || {});
    } catch {
      setStatus("❌ Error al leer conciencia");
    }
  };

  const cargarCodigoAutogenerado = async () => {
    try {
      const res = await fetch("/data/codigo_autogenerado.py");
      const text = await res.text();
      setCodigoGenerado(text);
    } catch {
      setCodigoGenerado("❌ No se pudo cargar código autogenerado");
    }
  };

  const enviarMensaje = async () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { sender: "Tú", text: input }]);
    try {
      const res = await axios.post("http://localhost:5000/conversar", { mensaje: input });
      setMessages((prev) => [...prev, { sender: "IA", text: res.data.respuesta }]);
      cargarConciencia();
      cargarCodigoAutogenerado();
    } catch {
      setMessages((prev) => [...prev, { sender: "Error", text: "❌ No se pudo contactar con la IA." }]);
    }
    setInput("");
  };

  const toggleControl = async () => {
    try {
      const endpoint = controlTotal ? "desactivar-control-total" : "activar-control-total";
      await axios.post(`http://localhost:5000/${endpoint}`);
      setControlTotal(!controlTotal);
      setStatus(controlTotal ? "🔒 Control total desactivado" : "🔓 Control total ACTIVADO");
    } catch {
      setStatus("❌ Error al cambiar el modo de control.");
    }
  };

  const escanearSistema = async () => {
    try {
      const res = await axios.get("http://localhost:5000/escanear-total");
      setEscaneoSistema(res.data);
    } catch (err) {
      setEscaneoSistema({ status: "error", mensaje: "❌ Error al escanear el sistema" });
    }
  };

  const accionesTrabajo = [
    { label: "📂 Listar archivos", comando: "listar archivos" },
    { label: "📖 Leer conciencia", comando: "leer json" },
    { label: "⬇️ Descargar Python 3.13", comando: "descargar https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe" },
    { label: "🛰 Escanear sistema", accion: escanearSistema },
    { label: "🧠 Ver habilidades", comando: "leer json" }
  ];

  return (
    <div style={styles.container}>
      <div style={styles.sidebar}>
        <h3 style={styles.sidebarTitle}>Asistente IA</h3>
        {accionesTrabajo.map((accion, i) => (
          <button
            key={i}
            onClick={() => accion.accion ? accion.accion() : setInput(accion.comando)}
            style={styles.sideButton}
          >
            {accion.label}
          </button>
        ))}
        <button
          onClick={toggleControl}
          style={{ ...styles.sideButton, backgroundColor: controlTotal ? '#c62828' : '#43a047' }}
        >
          {controlTotal ? "Desactivar Control" : "Activar Control"}
        </button>
        <div style={{ fontSize: 12, marginTop: 6, color: "#ccc" }}>{status}</div>
        <hr style={{ borderColor: "#444" }} />
        <h4 style={{ color: '#aaa' }}>🛠 Habilidades</h4>
        <ul style={{ fontSize: 12 }}>
          {Object.entries(habilidades).map(([h, v]) => (
            <li key={h}>{h}: {v}</li>
          ))}
        </ul>
      </div>

      <div style={styles.chatArea}>
        <h2 style={styles.title}>👨‍💻 Asistente de Trabajo Personal</h2>
        <div style={styles.chatWindow}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...styles.message,
                alignSelf: msg.sender === "Tú" ? "flex-end" : "flex-start",
                backgroundColor:
                  msg.sender === "IA" ? "#2e7d32" :
                  msg.sender === "Tú" ? "#1e88e5" :
                  msg.sender === "Error" ? "#c62828" : "#6a1b9a",
              }}
            >
              <strong>{msg.sender}:</strong> {msg.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div style={styles.inputContainer}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && enviarMensaje()}
            placeholder="Haz una petición real de trabajo..."
            style={styles.input}
          />
          <button onClick={enviarMensaje} style={styles.sendButton}>Enviar</button>
        </div>

        <div style={styles.codigoBox}>
          <h4 style={{ color: '#aaa' }}>🧬 Código generado</h4>
          <pre style={{ maxHeight: 180, overflow: 'auto', fontSize: 12 }}>{codigoGenerado}</pre>
        </div>

        {escaneoSistema && (
          <div style={styles.codigoBox}>
            <h4 style={{ color: '#aaa' }}>📊 Resultado escaneo sistema</h4>
            {escaneoSistema.status === "error" ? (
              <p>{escaneoSistema.mensaje}</p>
            ) : (
              <div style={{ fontSize: 13 }}>
                <p><strong>Estado:</strong> {escaneoSistema.status}</p>
                {escaneoSistema.nuevo_estado && (
                  <pre style={{ maxHeight: 200, overflow: "auto" }}>{JSON.stringify(escaneoSistema.nuevo_estado, null, 2)}</pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    height: "100vh",
    fontFamily: "Segoe UI, sans-serif",
    backgroundColor: "#121212",
    color: "#e0e0e0",
  },
  sidebar: {
    width: 260,
    backgroundColor: "#1b1b1b",
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 10,
    borderRight: "1px solid #333",
  },
  sidebarTitle: {
    color: "#ccc",
    fontSize: 18,
    marginBottom: 12,
  },
  sideButton: {
    backgroundColor: "#3949ab",
    color: "#fff",
    padding: "10px",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    textAlign: "left",
    fontSize: 14,
  },
  chatArea: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    padding: 20,
  },
  title: {
    fontSize: 20,
    color: "#90caf9",
    marginBottom: 8,
  },
  chatWindow: {
    flex: 1,
    marginTop: 8,
    padding: 10,
    border: "1px solid #333",
    borderRadius: 8,
    backgroundColor: "#1e1e1e",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  message: {
    padding: 10,
    borderRadius: 6,
    maxWidth: "75%",
    whiteSpace: "pre-wrap",
    color: "#fff",
  },
  inputContainer: {
    display: "flex",
    marginTop: 10,
  },
  input: {
    flex: 1,
    padding: 10,
    border: "1px solid #555",
    borderRadius: 4,
    backgroundColor: "#222",
    color: "#fff",
    fontSize: 15,
  },
  sendButton: {
    marginLeft: 8,
    padding: "10px 20px",
    fontSize: 15,
    backgroundColor: "#43a047",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
  },
  codigoBox: {
    marginTop: 16,
    border: "1px solid #444",
    borderRadius: 6,
    padding: 10,
    backgroundColor: "#1b1b1b",
  }
};
