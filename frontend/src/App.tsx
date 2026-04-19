import { Navigate, Route, Routes } from "react-router-dom";

import AuthCallback from "./pages/AuthCallback";
import Login from "./pages/Login";
import Projects from "./pages/Projects";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/projects" element={<Projects />} />
      <Route path="*" element={<div className="p-8">Not found</div>} />
    </Routes>
  );
}
