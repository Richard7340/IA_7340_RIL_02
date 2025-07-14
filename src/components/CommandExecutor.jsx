
import React, { useState } from 'react';
import axios from 'axios';

export default function CommandExecutor({ controlTotal }) {
    const [comando, setComando] = useState('');
    const [resultado, setResultado] = useState('');

    const ejecutar = async () => {
        try {
            const res = await axios.post('http://localhost:5000/ejecutar-comando', { comando });
            setResultado(res.data.resultado || 'Comando ejecutado.');
        } catch {
            setResultado('Error ejecutando comando.');
        }
    };

    if (!controlTotal) return null;

    return (
        <div className="command-executor">
            <h3>Terminal de Comandos</h3>
            <input value={comando} onChange={e => setComando(e.target.value)} placeholder="Escribe un comando..." />
            <button onClick={ejecutar}>Ejecutar</button>
            {resultado && <pre className="resultado">{resultado}</pre>}
        </div>
    );
}
