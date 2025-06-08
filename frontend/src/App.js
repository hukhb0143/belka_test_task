import './App.css';
import axios from 'axios';
import AuthForm from './ui/auth-form/auth-form';
import ConcentrateQualitySystem from './ui/input-form/input-form';
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';


export const backend_url = 'http://localhost:8000';
console.log(backend_url)

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
              <Navigate to="/input-form" /> : 
              <AuthForm onLoginSuccess={handleLoginSuccess} />
          } 
        />
        <Route 
          path="/input-form" 
          element={
            isAuthenticated ? 
              <ConcentrateQualitySystem onLogout={handleLogout} /> : 
              <Navigate to="/login" />
          } 
        />
        <Route path="*" element={<Navigate to={isAuthenticated ? "/input-form" : "/login"} />} />
      </Routes>
    </Router>
  );
};


export default App;
