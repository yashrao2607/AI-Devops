import { useState } from 'react';
import { Shell, NavItem } from './components/layout/Shell.tsx';
import { Dashboard } from './pages/Dashboard.tsx';
import { Analyze } from './pages/Analyze.tsx';
import { Repositories } from './pages/Repositories.tsx';
import { Runs } from './pages/Runs.tsx';
import { Findings } from './pages/Findings.tsx';
import { Agents } from './pages/Agents.tsx';
import { Reports } from './pages/Reports.tsx';
import { SettingsPage } from './pages/Settings.tsx';

export default function App() {
  const [currentTab, setCurrentTab] = useState<NavItem>('overview');

  const renderContent = () => {
    switch (currentTab) {
      case 'overview':
        return <Dashboard />;
      case 'analyze':
        return <Analyze />;
      case 'repositories':
        return <Repositories />;
      case 'runs':
        return <Runs />;
      case 'findings':
        return <Findings />;
      case 'agents':
        return <Agents />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Shell currentTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </Shell>
  );
}
