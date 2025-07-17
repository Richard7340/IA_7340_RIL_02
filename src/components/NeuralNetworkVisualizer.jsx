// src/components/NeuralNetworkVisualizer.jsx
import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/solid"; // Asumiendo que usas Heroicons para iconos

// Definición de nodos y enlaces basada en el funcionamiento de la IA
const nodesData = [
  { id: "GPT", label: "GPT Engine", color: "#3B82F6", group: "core" }, // Azul para IA principal
  { id: "Conciencia", label: "Conciencia", color: "#10B981", group: "core" }, // Verde para evolución
  { id: "Memoria", label: "Memoria", color: "#EAB308", group: "storage" }, // Amarillo para almacenamiento
  { id: "Autoprogramar", label: "Autoprogramar", color: "#EF4444", group: "execution" }, // Rojo para autoprogramación
  { id: "Escaneo", label: "Escaneo Sistema", color: "#8B5CF6", group: "analysis" }, // Morado para escaneo
  { id: "Descargas", label: "Descargas", color: "#EC4899", group: "io" }, // Rosa para I/O
  { id: "SistemaRutas", label: "Sistema Rutas", color: "#6D28D9", group: "io" }, // Violeta para rutas
  { id: "Evolucion", label: "Evolución", color: "#14B8A6", group: "core" }, // Teal para evolución
  { id: "Ejecucion", label: "Ejecución Comandos", color: "#F97316", group: "execution" }, // Naranja para ejecución
];

const linksData = [
  { source: "GPT", target: "Conciencia", value: 2 },
  { source: "Conciencia", target: "Memoria", value: 3 },
  { source: "Conciencia", target: "Evolucion", value: 2 },
  { source: "GPT", target: "Autoprogramar", value: 1 },
  { source: "Autoprogramar", target: "Ejecucion", value: 2 },
  { source: "Ejecucion", target: "SistemaRutas", value: 1 },
  { source: "Ejecucion", target: "Descargas", value: 1 },
  { source: "Conciencia", target: "Escaneo", value: 2 },
  { source: "Escaneo", target: "Memoria", value: 1 },
];

export default function NeuralNetworkVisualizer({ actionsLog = [], onActionTrigger }) {
  const svgRef = useRef(null);
  const [simulation, setSimulation] = useState(null);
  const [activeNodes, setActiveNodes] = useState(new Set());
  const [activePaths, setActivePaths] = useState([]);
  const [expandedLog, setExpandedLog] = useState(true);
  const [logs, setLogs] = useState(actionsLog); // Estado para logs, inicializado con prop

  // Actualizar logs cuando cambie la prop
  useEffect(() => {
    setLogs(actionsLog);
  }, [actionsLog]);

  // Inicializar D3 force simulation
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const width = svg.node().clientWidth;
    const height = svg.node().clientHeight;

    // Limpiar SVG previo
    svg.selectAll("*").remove();

    // Crear simulación de fuerza
    const sim = d3.forceSimulation(nodesData)
      .force("link", d3.forceLink(linksData).id(d => d.id).distance(150).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(50));

    // Enlaces (líneas brillantes)
    const links = svg.append("g")
      .selectAll("line")
      .data(linksData)
      .enter()
      .append("line")
      .attr("stroke", "#4B5563") // Gris oscuro base
      .attr("stroke-width", d => d.value)
      .attr("class", "link");

    // Nodos (círculos con etiquetas)
    const nodes = svg.append("g")
      .selectAll("g")
      .data(nodesData)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    nodes.append("circle")
      .attr("r", 20)
      .attr("fill", d => d.color)
      .attr("stroke", "#1F2937")
      .attr("stroke-width", 2);

    nodes.append("text")
      .attr("dy", 4)
      .attr("dx", 25)
      .attr("fill", "#D1D5DB")
      .attr("font-size", 12)
      .text(d => d.label);

    // Tick function para actualizar posiciones
    sim.on("tick", () => {
      links
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      nodes
        .attr("transform", d => `translate(${d.x}, ${d.y})`);
    });

    setSimulation(sim);

    // Funciones de drag
    function dragstarted(event, d) {
      if (!event.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) sim.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => sim.stop(); // Cleanup
  }, []);

  // Animar nodos y paths cuando ocurren acciones
  useEffect(() => {
    if (onActionTrigger) {
      // Ejemplo: onActionTrigger({ node: "GPT", path: ["GPT", "Conciencia"] }) para trigger
      const handleTrigger = ({ node, path }) => {
        setActiveNodes(prev => new Set([...prev, node]));
        if (path) setActivePaths(prev => [...prev, path]);

        // Desactivar después de 2s
        setTimeout(() => {
          setActiveNodes(prev => {
            const newSet = new Set(prev);
            newSet.delete(node);
            return newSet;
          });
          setActivePaths(prev => prev.filter(p => p !== path));
        }, 2000);
      };

      // Asumir que onActionTrigger es un emitter o callback; ajusta según integración
      // Por ahora, simular con logs nuevos
      if (logs.length > 0) {
        const lastLog = logs[logs.length - 1];
        // Mapear log a nodo/path basado en keywords (customiza según tus logs)
        let triggeredNode = "GPT"; // Default
        if (lastLog.includes("escanear")) triggeredNode = "Escaneo";
        else if (lastLog.includes("descargar")) triggeredNode = "Descargas";
        // ... agregar más mapeos

        handleTrigger({ node: triggeredNode, path: [triggeredNode, "Conciencia"] });
      }
    }
  }, [logs, onActionTrigger]);

return (
  <div className="flex h-screen bg-gray-900 text-gray-200">
    {/* Sidebar */}
    <div className="w-64 bg-gray-800 p-4 flex flex-col gap-2 border-r border-gray-700">
      <h3 className="text-lg font-semibold text-gray-300 mb-3">Asistente IA</h3>
      {accionesTrabajo.map((accion, i) => (
        <button
          key={i}
          onClick={() => accion.accion ? accion.accion() : setInput(accion.comando)}
          className="bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-500 text-left text-sm"
        >
          {accion.label}
        </button>
      ))}
      <button
        onClick={toggleControl}
        className={`${controlTotal ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'} text-white py-2 px-4 rounded-md text-sm`}
      >
        {controlTotal ? "Desactivar Control" : "Activar Control"}
      </button>
      <div className="text-xs text-gray-400 mt-1">{status}</div>
      <hr className="border-gray-600 my-2" />
      <h4 className="text-sm text-gray-400">🛠 Habilidades</h4>
      <ul className="text-xs space-y-1">
        {Object.entries(habilidades).map(([h, v]) => (
          <li key={h}>{h}: {v}</li>
        ))}
      </ul>
    </div>

    {/* Área Principal: Chat + Visualizador Neuronal */}
    <div className="flex-1 flex flex-col p-5">
      <h2 className="text-xl font-bold text-blue-300 mb-2">👨‍💻 Asistente de Trabajo Personal</h2>
      
      {/* Integración del Visualizador (ocupa mitad superior o ajusta según prefieras) */}
      <NeuralNetworkVisualizer 
        actionsLog={messages.map(msg => msg.text)}  // Pasa logs para animaciones
        onActionTrigger={(action) => console.log('Acción trigger:', action)}  // Callback para triggers personalizados
      />

      {/* Chat Window */}
      <div className="flex-1 mt-4 p-4 bg-gray-800 rounded-lg overflow-y-auto flex flex-col gap-2 shadow-md">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-md max-w-[75%] text-white text-sm ${
              msg.sender === "Tú" ? "self-end bg-blue-600" :
              msg.sender === "IA" ? "self-start bg-green-600" :
              msg.sender === "Error" ? "self-start bg-red-600" : "self-start bg-purple-600"
            }`}
          >
            <strong>{msg.sender}:</strong> {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex mt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && enviarMensaje()}
          placeholder="Haz una petición real de trabajo..."
          className="flex-1 p-3 bg-gray-700 border border-gray-600 rounded-l-md text-white focus:outline-none focus:border-blue-500"
        />
        <button onClick={enviarMensaje} className="bg-green-600 text-white px-5 rounded-r-md hover:bg-green-500">
          Enviar
        </button>
      </div>

      {/* Código Generado */}
      <div className="mt-4 p-4 bg-gray-800 rounded-lg">
        <h4 className="text-sm text-gray-400">🧬 Código generado</h4>
        <pre className="max-h-40 overflow-auto text-xs text-gray-300">{codigoGenerado}</pre>
      </div>

      {/* Escaneo Sistema */}
      {escaneoSistema && (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg">
          <h4 className="text-sm text-gray-400">📊 Resultado escaneo sistema</h4>
          {escaneoSistema.status === "error" ? (
            <p>{escaneoSistema.mensaje}</p>
          ) : (
            <div className="text-sm">
              <p><strong>Estado:</strong> {escaneoSistema.status}</p>
              {escaneoSistema.nuevo_estado && (
                <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(escaneoSistema.nuevo_estado, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  </div>
);
}

// Uso en IAWorkAssistant: <NeuralNetworkVisualizer actionsLog={messages.map(m => m.text)} onActionTrigger={handleAction} />
