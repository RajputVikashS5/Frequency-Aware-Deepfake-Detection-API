import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalyzePage from './pages/AnalyzePage';
import ResultsPage from './pages/ResultsPage';
import HistoryPage from './pages/HistoryPage';
import Methodology from './pages/Methodology';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Detector from './pages/Detector';
import AblationStudy from './pages/AblationStudy';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/results/:analysisId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/about" element={<Methodology />} />
        <Route path="/methodology" element={<Methodology />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/legacy-detector" element={<Detector />} />
        <Route path="/ablation" element={<AblationStudy />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
