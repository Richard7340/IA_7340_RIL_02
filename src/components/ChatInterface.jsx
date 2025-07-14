
import React, { useState } from 'react';
import axios from 'axios';

export default function ChatInterface({ controlTotal }) {
    const [input, setInput] = useState('');
    const [chat, setChat] = useState([]);

    const enviarMensaje = async () => {
        if (!input.trim()) return;
        const nuevoChat = [...chat, { from: 'user', text: input }];
        setChat(nuevoChat);
        setInput('');
        try {
            const res = await axios.post('http://localhost:5000/conversar', { mensaje: input });
            setChat([...nuevoChat, { from: 'ia', text: res.data.respuesta }]);
        } catch (err) {
            setChat([...nuevoChat, { from: 'ia', text: 'Error al contactar con el backend.' }]);
        }
    };

    return (
        <div className="chat-interface">
            <div className="chat-log">
                {chat.map((msg, i) => (
                    <div key={i} className={msg.from === 'user' ? 'chat-user' : 'chat-ia'}>
                        <strong>{msg.from === 'user' ? 'Tú' : 'IA'}:</strong> {msg.text}
                    </div>
                ))}
            </div>
            <input value={input} onChange={e => setInput(e.target.value)} placeholder="Escribe un mensaje..." />
            <button onClick={enviarMensaje}>Enviar</button>
        </div>
    );
}
