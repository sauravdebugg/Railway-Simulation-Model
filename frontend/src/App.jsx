import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import LiveMap from "@/pages/LiveMap";
import Simulation from "@/pages/Simulation";
import AIPrediction from "@/pages/AIPrediction";
import Analytics from "@/pages/Analytics";
import Reports from "@/pages/Reports";
import Settings from "@/pages/Settings";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<LiveMap />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/ai-prediction" element={<AIPrediction />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
        <Toaster theme="dark" position="top-right" richColors />
      </BrowserRouter>
    </div>
  );
}

export default App;
