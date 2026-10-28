import { useState, useEffect } from 'react';
import { Shell, NavItem } from './components/layout/Shell.tsx';
import { Dashboard } from './pages/Dashboard.tsx';
import { Analyze } from './pages/Analyze.tsx';
import { Repositories } from './pages/Repositories.tsx';
import { Runs } from './pages/Runs.tsx';
import { Findings } from './pages/Findings.tsx';
import { Agents } from './pages/Agents.tsx';
import { Observability } from './pages/Observability.tsx';
import { Evaluation } from './pages/Evaluation.tsx';
import { Reports } from './pages/Reports.tsx';
import { SettingsPage } from './pages/Settings.tsx';

export default function App() {
  const parseTabFromLocation = (): NavItem => {
    const validTabs: NavItem[] = ['overview', 'analyze', 'repositories', 'runs', 'findings', 'agents', 'observability', 'evaluation', 'reports', 'settings'];
    
    // Check hash first (e.g. #analyze or #analyze?repo=...)
    const hash = window.location.hash.replace(/^#/, '').split('?')[0].toLowerCase();
    if (validTabs.includes(hash as NavItem)) return hash as NavItem;
    
    // Check pathname (e.g. /analyze or /analyze?repo=...)
    const path = window.location.pathname.replace(/^\//, '').split('?')[0].toLowerCase();
    if (validTabs.includes(path as NavItem)) return path as NavItem;
    
    return 'overview';
  };

  const [currentTab, setCurrentTab] = useState<NavItem>(parseTabFromLocation());

  useEffect(() => {
    const syncTab = () => {
      const tab = parseTabFromLocation();
      setCurrentTab(tab);
    };

    window.addEventListener('hashchange', syncTab);
    window.addEventListener('popstate', syncTab);
    window.addEventListener('deploysafe-navigate', syncTab);

    return () => {
      window.removeEventListener('hashchange', syncTab);
      window.removeEventListener('popstate', syncTab);
      window.removeEventListener('deploysafe-navigate', syncTab);
    };
  }, []);

  const handleTabChange = (tab: NavItem) => {
    setCurrentTab(tab);
    window.location.hash = tab === 'overview' ? '' : `#${tab}`;
  };

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
      case 'observability':
        return <Observability />;
      case 'evaluation':
        return <Evaluation />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Shell currentTab={currentTab} onSelectTab={handleTabChange}>
      {renderContent()}
    </Shell>
  );
}
