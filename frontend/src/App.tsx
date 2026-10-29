import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout.tsx';
import { Dashboard } from './pages/Dashboard.tsx';
import { Employees } from './pages/Employees.tsx';
import { TeamConstructor } from './pages/TeamConstructor.tsx';
import { AbsencesCalendar } from './pages/AbsencesCalendar.tsx';
import { Projects } from './pages/Projects.tsx';
import { Analytics } from './pages/Analytics.tsx';
import { GanttChart } from './pages/GanttChart.tsx';
import { Settings } from './pages/Settings.tsx';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="employees" element={<Employees />} />
        <Route path="projects" element={<Projects />} />
        <Route path="constructor" element={<TeamConstructor />} />
        <Route path="calendar" element={<AbsencesCalendar />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="gantt" element={<GanttChart />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
