import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";


import Login from "./pages/Login";
import Register from "./pages/Register";
import ProtectedRoute from "./components/ProtectedRoute";


import UserPortal from "./pages/UserPortal";
import Dashboard from "./pages/Dashboard";
import Audit from "./pages/Audit";
import Admin from "./pages/Admin";


function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />


      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />


      <Route
        path="/portal"
        element={
          <ProtectedRoute>
            <UserPortal />
          </ProtectedRoute>
        }
      />


      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />


      <Route
        path="/audit"
        element={
          <ProtectedRoute>
            <Audit />
          </ProtectedRoute>
        }
      />


      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <Admin />
          </ProtectedRoute>
        }
      />


      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}


export default App;




