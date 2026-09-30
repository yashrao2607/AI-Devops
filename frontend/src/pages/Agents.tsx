import React from 'react';
import { Bot } from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge } from '../components/common/Badge.tsx';

export const Agents: React.FC = () => {
  const agents = [
    {
      name: 'Orchestrator Agent',
      role: 'CrewAI Flow Controller',
      desc: 'Coordinates repository analysis, formulates dynamic plans based on discovered tech stack, manages thread pool execution, and sequences Critic review.',
      phase: 'Phase 3 Active',
      tools: ['ThreadPoolExecutor', 'RepositoryTools', 'ChromaVectorStore']
    },
    {
      name: 'Code Analysis Agent',
      role: 'AST & Deployment Risk Inspector',
      desc: 'Inspects changed files and source code for deployment risks: unhandled exceptions, breaking API signatures, and hardcoded localhost/dev endpoints.',
      phase: 'Phase 3 Active',
      tools: ['get_file_content', 'get_git_diff', 'code_check']
    },
    {
      name: 'Dependency Agent',
      role: 'Supply Chain Inspector',
      desc: 'Parses requirements.txt, package.json, pyproject.toml to flag unpinned versions, missing lockfiles, and hazardous upgrades.',
      phase: 'Phase 3 Active',
      tools: ['get_dependency_manifests']
    },
    {
      name: 'Configuration Agent',
      role: 'Docker & Environment Inspector',
      desc: 'Analyzes Dockerfiles, compose files, YAML manifests, and environment variables to flag unpinned base images and missing production configs.',
      phase: 'Phase 3 Active',
      tools: ['get_file_content', 'docker_check']
    },
    {
      name: 'Test Agent',
      role: 'Regression & Safety Inspector',
      desc: 'Discovers test suites, safely runs sandboxed pytest runners, and strictly distinguishes observed test results from inferred test coverage.',
      phase: 'Phase 3 Active',
      tools: ['run_tests_safe', 'get_test_files']
    },
    {
      name: 'Documentation / RAG Agent',
      role: 'Chroma Vector Store Investigator',
      desc: 'Queries indexed repository documentation and correlates documented deployment requirements (e.g. REDIS_URL) against actual configuration manifests.',
      phase: 'Phase 3 Active',
      tools: ['search_repository_context', 'ChromaRetriever']
    },
    {
      name: 'Security Analysis Agent',
      role: 'Static & Secret Scanner',
      desc: 'Runs deterministic static scanners and regex secret detectors with automatic credential masking (***REDACTED_SECRET***).',
      phase: 'Phase 3 Active',
      tools: ['run_security_scan', 'BanditScanner', 'SecretScanner']
    },
    {
      name: 'Critic Agent',
      role: 'Ground-Truth Gatekeeper & Deduplicator',
      desc: 'Cross-verifies all findings against concrete repository evidence, rejects hallucinations, marks duplicates, and audits confidence levels.',
      phase: 'Phase 3 Active',
      tools: ['verify_file_existence', 'anti_hallucination_gate']
    },
    {
      name: 'Report Synthesis Agent',
      role: 'Executive Summary Formatter',
      desc: 'Compiles validated findings, computes true severity counts, and generates actionable deployment-readiness intelligence reports.',
      phase: 'Phase 3 Active',
      tools: ['summarize_report']
    }
  ];

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Bot className="w-6 h-6 text-emerald-400" />
          CrewAI Multi-Agent Roster
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Specialized autonomous agents collaborating with deterministic tools and Critic validation in Phase 3.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <Card key={agent.name} className="border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                  <span className="text-xs font-mono text-emerald-400">{agent.role}</span>
                </div>
                <Badge variant="success">
                  {agent.phase}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-3 leading-relaxed">{agent.desc}</p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <span className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Invoked Tools</span>
              <div className="flex flex-wrap gap-1">
                {agent.tools.map((tool) => (
                  <span
                    key={tool}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
