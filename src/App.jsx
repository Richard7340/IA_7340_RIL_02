import React from "react";
import "./App.css";
import ChatInterface from "./ChatInterface";
import ControlPanel from "./components/ControlPanel";

function App() {
  return (
    <div className="App">
      <h1>Terminal IA Autónoma</h1>
      <ControlPanel />
      <ChatInterface />
    </div>
  );
}

export default App;
