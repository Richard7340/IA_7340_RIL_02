
import React from 'react';

export default function SystemStatus({ controlTotal }) {
    return (
        <div className="system-status">
            <h3>Estado del Sistema</h3>
            <p>🧠 Control Total: {controlTotal ? '🟢 Activado' : '🔴 Desactivado'}</p>
        </div>
    );
}
