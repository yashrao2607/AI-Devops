import React from 'react';
import { Bot } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

export const Agents: React.FC = () => {
  const agents = [
    {
      name: 'Repository Readiness Agent',
      role: 'Foundation Inspector',
      desc: 'Performs baseline deployment artifact checks, repository discovery, and structured Pydantic assessment.',
      phase: 'Phase 1'
    },
    {
      name: 'Code Analysis Agent',
      role: 'AST & Pattern Inspector',
      desc: 'Analyzes changed files, exception handling, breaking API changes, and hardcoded secrets.',
      phase: 'Phase 3'
    },
    {
      name: 'Dependency Agent',
      role: 'Supply Chain Inspector',
      desc: 'Checks added/removed packages, version changes, license conflicts, and security advisories.',
      phase: 'Phase 3'
    },
    {
      name: 'Configuration Agent',
      role: 'Environment & Docker Inspector',
      desc: 'Validates .env files, Dockerfiles, YAML manifests, and production configuration drift.',
      phase: 'Phase 3'
    },
    {
      name: 'Test Agent',
      role: 'Regression & Coverage Inspector',
      desc: 'Verifies test execution, reports failed tests, and flags missing regression coverage.',
      phase: 'Phase 3'
    },
    {
      name: 'Critic Agent',
      role: 'Reflection & Evidence Validator',
      desc: 'Cross-checks AI findings against repository citations, removes duplicates, and flags false positives.',
      phase: 'Phase 3'
    },
  ];

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Bot className="w-6 h-6 text-emerald-400" />
          CrewAI Multi-Agent Roster
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Specialized autonomous agents collaborating within the DeploySafe deployment readiness pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => (
          <Card key={agent.name} className="border-slate-800">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                <span className="text-xs font-mono text-emerald-400">{agent.role}</span>
              </div>
              <Badge variant={agent.phase === 'Phase 1' ? 'success' : 'neutral'}>
                {agent.phase === 'Phase 1' ? 'PHASE 1 ACTIVE' : 'PHASE 3 ROADMAP'}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-3">{agent.desc}</p>
          </Card>
        ))}
      </div>
    </div>
  );
};
