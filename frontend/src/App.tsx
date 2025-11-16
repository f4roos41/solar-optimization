import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';
import AnalysisWorkbench from './pages/AnalysisWorkbench';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:projectId" element={<ProjectView />} />
          <Route path="/project/:projectId/analysis" element={<AnalysisWorkbench />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
