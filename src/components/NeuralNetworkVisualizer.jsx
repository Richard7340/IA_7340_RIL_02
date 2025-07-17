// src/components/NeuralNetworkVisualizer.jsx
import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/solid";

// Definición de nodos y enlaces basada en el funcionamiento de la IA
const nodesData = [
  { id: "GPT", label: "GPT Engine", color: "#3B82F6", group: "core" },
  { id: "Conciencia", label: "#Conciencia", color: "#10B981", group: "core" },
  { id: "Memoria", label: "#Memoria", color: "#EAB308", group: "storage" },
  { id: "Autoprogramar", label: "Autoprogramar", color: "#EF4444", group: "execution" },
  { id: "Escaneo", label: "Escaneo Sistema", color: "#8B5CF6", group: "analysis" },
  { id: "Descargas", label: "Descargas", color: "#EC4899", group: "io" },
  { id: "SistemaRutas", label: "Sistema Rutas", color: "#6D28D9", group: "io" },
  { id: "Evolucion", label: "Evolución", color: "#14B8A6", group: "core" },
  { id: "Ejecucion", label: "Ejecución Comandos", color: "#F97316", group: "execution" },
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

export default function NeuralNetworkVisualizer({
  actionsLog = [],
  onActionTrigger,
  accionesTrabajo = [],
  setInput = () => {},
  toggleControl = () => {},
  controlTotal = false,
  status = "",
  habilidades = {},
  messages = [],
  messagesEndRef,
  input = "",
  enviarMensaje = () => {},
  codigoGenerado = "",
  escaneoSistema = null,
}) {
  const svgRef = useRef(null);
  const internalEndRef = useRef(null);
  const endRef = messagesEndRef || internalEndRef;
  const [simulation, setSimulation] = useState(null);
  const [activeNodes, setActiveNodes] = useState(new Set());
  const [activePaths, setActivePaths] = useState([]);
  const [expandedLog, setExpandedLog] = useState(true);
  const [logs, setLogs] = useState(actionsLog);

  const prevTrigger = useRef(null);

  // Actualizar logs cuando cambia la prop
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
      .force("collide", d3.forceCollide(30));

    // Añadir elementos de enlaces
    const link = svg.append("g")
      .selectAll(".link")
      .data(linksData)
      .enter()
      .append("line")
      .classed("link", true)
      .attr("stroke", "#4B5563")
      .attr("stroke-width", d => d.value);

    // Añadir elementos de nodos
    const node = svg.append("g")
      .selectAll(".node")
      .data(nodesData)
      .enter()
      .append("g")
      .classed("node", true)
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    node.append("circle")
      .attr("r", 20)
      .attr("fill", d => d.color);

    node.append("text")
      .text(d => d.label)
      .attr("dy", ".35em")
      .attr("text-anchor", "middle")
      .attr("fill", "#FFFFFF");

    // Función de tick
    sim.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x}, ${d.y})`);
    });

    setSimulation(sim);

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

    return () => sim.stop();
  }, []);

  // Actualizar highlights en nodos y paths activos
  useEffect(() => {
    const svg = d3.select(svgRef.current);

    // Highlight nodos activos
    svg.selectAll(".node circle")
      .attr("fill", d => activeNodes.has(d.id) ? "#FFD700" : d.color);

    // Highlight paths activos
    svg.selectAll(".link")
      .attr("stroke", d => {
        return activePaths.some(path => 
          path.includes(d.source.id) && path.includes(d.target.id)
        ) ? "#FFD700" : "#4B5563";
      })
      .attr("stroke-width", d => {
        return activePaths.some(path => 
          path.includes(d.source.id) && path.includes(d.target.id)
        ) ? d.value * 2 : d.value;
      });
  }, [activeNodes, activePaths]);

  // Manejo de triggers con prevención de loop
  useEffect(() => {
    if (onActionTrigger && onActionTrigger !== prevTrigger.current) {
      const handleTrigger = (trigger) => {
        // Activar basados en trigger (ej. desde JSON action)
        setActiveNodes(new Set([trigger.nodeId || "GPT"])); // Default a GPT si no
        setActivePaths([[trigger.source || "GPT", trigger.target || "Conciencia"]]);

        if (simulation) {
          simulation.alphaTarget(0.1).restart();
        }

        // Limpiar después
        setTimeout(() => {
          setActiveNodes(new Set());
          setActivePaths([]);
        }, 2000);
      };

      handleTrigger(onActionTrigger);
      prevTrigger.current = onActionTrigger;
    }
  }, [onActionTrigger, simulation]);

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Visualizador de Red Neuronal */}
      <svg ref={svgRef} className="flex-1" />

      {/* Chat Window */}
      <div className="h-1/2 p-4 overflow-y-auto bg-gray-800 border-t border-gray-700">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="mb-2"
            >
              <span className="font-bold">{msg.sender}:</span> {msg.text}
            </motion.p>
          ))}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      {/* Sección de Logs Expandible (acciones de JSON/IA) */}
      <div className="p-4 bg-gray-800 border-t border-gray-700">
        <button
          onClick={() => setExpandedLog(!expandedLog)}
          className="flex items-center w-full text-left font-semibold mb-2"
        >
          Logs de Acciones y JSON Interacciones
          {expandedLog ? (
            <ChevronUpIcon className="w-5 h-5 ml-2" />
          ) : (
            <ChevronDownIcon className="w-5 h-5 ml-2" />
          )}
        </button>
        {expandedLog && (
          <ul className="list-disc pl-5">
            {logs.map((log, i) => (
              <li key={i} className="mb-1">{log}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Sección de Estado del Sistema y Botones (mantenidos) */}
      <div className="p-4 bg-gray-800 border-t border-gray-700">
        <p className="font-bold mb-2">Estado del Sistema: {status}</p>
        <p className="mb-2">Control Total: {controlTotal ? 'Activo' : 'Inactivo'}</p>
        <button
          onClick={toggleControl}
          className="bg-blue-500 text-white p-2 rounded mr-2"
        >
          {controlTotal ? 'Desactivar Control Total' : 'Activar Control Total'}
        </button>
        {/* Botones para Acciones de Trabajo si hay */}
        {accionesTrabajo.length > 0 && (
          <div className="mt-2">
            <p className="font-semibold">Acciones Disponibles:</p>
            {accionesTrabajo.map((accion, i) => (
              <button key={i} onClick={() => console.log('Ejecutar', accion)} className="bg-green-500 text-white p-1 rounded mr-1">
                {accion}
              </button>
            ))}
          </div>
        )}
        {/* Mostrar Habilidades */}
        {Object.keys(habilidades).length > 0 && (
          <div className="mt-2">
            <p className="font-semibold">Habilidades:</p>
            <ul className="list-disc pl-5">
              {Object.entries(habilidades).map(([key, value]) => (
                <li key={key}>{key}: {value}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Input para enviar mensajes (chat) */}
      <div className="p-4 bg-gray-800 border-t border-gray-700">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              enviarMensaje();
            }
          }}
          placeholder="Escribe un mensaje..."
          className="w-full p-2 bg-gray-700 text-white rounded mb-2"
        />
        <button onClick={enviarMensaje} className="bg-purple-500 text-white p-2 rounded">
          Enviar
        </button>
      </div>
    </div>
  );
}
