import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '../pages/HomePage';
import AnalyzePage from '../pages/AnalyzePage';
import ResultsPage from '../pages/ResultsPage';
import HistoryPage from '../pages/HistoryPage';
import Methodology from '../pages/Methodology';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';

export const routesConfig = [
  { path: '/', element: <HomePage />, label: 'Home' },
  { path: '/analyze', element: <AnalyzePage />, label: 'Analyze' },
  { path: '/results/:analysisId', element: <ResultsPage />, label: 'Results' },
  { path: '/history', element: <HistoryPage />, label: 'History' },
  { path: '/about', element: <Methodology />, label: 'About & Methodology' },
  { path: '/methodology', element: <Methodology />, label: 'Methodology' },
  { path: '/login', element: <LoginPage />, label: 'Login' },
  { path: '/register', element: <RegisterPage />, label: 'Register' },
  { path: '*', element: <Navigate to="/" replace /> },
];

export default function AppRoutes() {
  return (
    <Routes>
      {routesConfig.map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
    </Routes>
  );
}
