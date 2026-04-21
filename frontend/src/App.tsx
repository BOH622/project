import { Navigate, Route, Routes } from "react-router-dom";

import ImpersonationBanner from "./components/ImpersonationBanner";
import AuthCallback from "./pages/AuthCallback";
import Inventory from "./pages/Inventory";
import Login from "./pages/Login";
import Projects from "./pages/Projects";

export default function App() {
  return (
    <>
      <ImpersonationBanner />
      <Routes>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/projects" element={<Projects />} />
        {import.meta.env.DEV && <Route path="/inventory" element={<Inventory />} />}
        <Route path="*" element={<div className="p-8">Not found</div>} />
      </Routes>
    </>
  );
}
