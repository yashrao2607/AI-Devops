import React, { useState } from 'react';
import {
  FolderGit2,
  Search,
  Cpu,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  UploadCloud,
  Terminal,
  Layers,
  FileText,
  Folder,
  ShieldCheck,
  Play
} from 'lucide-react';
import { Card } from '../components/common/Card.tsx';
import { Badge, BadgeVariant } from '../components/common/Badge.tsx';
import { Button } from '../components/common/Button.tsx';

interface RepositorySnapshot {
  repository_id: string;
  repository_name: string;
  source_type: 'local' | 'github' | 'zip';
  root_path: string;
  branch?: string;
  commit_sha?: string;
  file_count: number;
  total_size_bytes: number;
}

interface IndexSummary {
  repository_id: string;
  files_discovered: number;
  files_indexed: number;
  files_skipped: number;
  chunks_created: number;
  embeddings_created: number;
  embedding_failures: number;
  total_size_bytes: number;
  duration_seconds: number;
  status: 'QUEUED' | 'INGESTING' | 'DISCOVERING' | 'CHUNKING' | 'EMBEDDING' | 'INDEXING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
}

interface SearchResult {
  chunk_id: string;
  relevance_score: number;
  file_path: string;
  line_start: number;
  line_end: number;
  category: string;
  language: string;
  content: string;
  commit_sha?: string;
}

interface SearchResponse {
  repository_id: string;
  query: string;
  status: 'FOUND' | 'LOW_RELEVANCE' | 'NOT_FOUND';
  results: SearchResult[];
  results_count: number;
}

interface DiscoveredFile {
  path: string;
  extension: string;
  category: string;
  language: string;
  size_bytes: number;
  is_indexable: boolean;
  skip_reason?: string;
}

export const Repositories: React.FC = () => {
  // Ingestion State
  const [sourceType, setSourceType] = useState<'local' | 'github' | 'zip'>('local');
  const [targetPath, setTargetPath] = useState('demo-repos/deploysafe-rag-demo');
  const [branch, setBranch] = useState('main');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  // Active Repository State
  const [snapshot, setSnapshot] = useState<RepositorySnapshot | null>(null);
  const [indexSummary, setIndexSummary] = useState<IndexSummary | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const [discoveredFiles, setDiscoveredFiles] = useState<DiscoveredFile[]>([]);
  const [showFilesModal, setShowFilesModal] = useState(false);

  // RAG Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<SearchResult | null>(null);
  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);

  // Handle Ingest
  const handleIngest = async () => {
    setIsIngesting(true);
    setIngestError(null);
    setSearchResponse(null);
    setSelectedEvidence(null);
    setIndexSummary(null);

    try {
      if (sourceType === 'zip') {
        if (!zipFile) {
          throw new Error('Please select a .zip archive file to upload.');
        }
        const formData = new FormData();
        formData.append('file', zipFile);
        const res = await fetch('/api/v1/repositories/ingest-zip', {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'ZIP ingestion failed');
        }
        const data: RepositorySnapshot = await res.json();
        setSnapshot(data);
      } else {
        const res = await fetch('/api/v1/repositories/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_type: sourceType,
            target: targetPath.trim(),
            branch: sourceType === 'github' ? branch.trim() : undefined,
          }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Repository ingestion failed');
        }
        const data: RepositorySnapshot = await res.json();
        setSnapshot(data);
      }
    } catch (err: any) {
      setIngestError(err.message || 'Failed to ingest repository');
    } finally {
      setIsIngesting(false);
    }
  };

  // Fetch Discovered Files
  const fetchDiscoveredFiles = async (repoId: string) => {
    try {
      const res = await fetch(`/api/v1/repositories/${encodeURIComponent(repoId)}/files`);
      if (res.ok) {
        const files: DiscoveredFile[] = await res.json();
        setDiscoveredFiles(files);
      }
    } catch (e) {
      console.error('Failed to load discovered files', e);
    }
  };

  // Trigger Indexing Pipeline
  const handleStartIndexing = async () => {
    if (!snapshot) return;
    setIsIndexing(true);
    setSearchResponse(null);
    setSelectedEvidence(null);

    try {
      // Optimistic initial state
      setIndexSummary({
        repository_id: snapshot.repository_id,
        files_discovered: snapshot.file_count,
        files_indexed: 0,
        files_skipped: 0,
        chunks_created: 0,
        embeddings_created: 0,
        embedding_failures: 0,
        total_size_bytes: snapshot.total_size_bytes,
        duration_seconds: 0,
        status: 'DISCOVERING',
      });

      const res = await fetch(`/api/v1/repositories/${encodeURIComponent(snapshot.repository_id)}/index`, {
        method: 'POST',
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Indexing failed');
      }

      const summary: IndexSummary = await res.json();
      setIndexSummary(summary);
      await fetchDiscoveredFiles(snapshot.repository_id);
    } catch (err: any) {
      setIndexSummary((prev) =>
        prev
          ? { ...prev, status: 'FAILED', error_message: err.message }
          : {
              repository_id: snapshot.repository_id,
              files_discovered: snapshot.file_count,
              files_indexed: 0,
              files_skipped: 0,
              chunks_created: 0,
              embeddings_created: 0,
              embedding_failures: 0,
              total_size_bytes: snapshot.total_size_bytes,
              duration_seconds: 0,
              status: 'FAILED',
              error_message: err.message,
            }
      );
    } finally {
      setIsIndexing(false);
    }
  };

  // Handle Semantic Search
  const handleSearch = async (queryText?: string) => {
    const q = queryText || searchQuery;
    if (!snapshot || !q.trim()) return;

    setIsSearching(true);
    try {
      const res = await fetch(`/api/v1/repositories/${encodeURIComponent(snapshot.repository_id)}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q.trim(),
          top_k: 5,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Search query failed');
      }

      const data: SearchResponse = await res.json();
      setSearchResponse(data);
      if (data.results && data.results.length > 0) {
        setSelectedEvidence(data.results[0]);
      } else {
        setSelectedEvidence(null);
      }
    } catch (err: any) {
      alert(`Search error: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  // Copy code chunk helper
  const handleCopyCode = (chunkId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(chunkId);
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const getStatusBadgeVariant = (status: string): BadgeVariant => {
    switch (status) {
      case 'COMPLETED':
      case 'FOUND':
        return 'success';
      case 'DISCOVERING':
      case 'CHUNKING':
      case 'EMBEDDING':
      case 'INDEXING':
        return 'info';
      case 'LOW_RELEVANCE':
        return 'moderate';
      case 'FAILED':
      case 'NOT_FOUND':
        return 'critical';
      default:
        return 'neutral';
    }
  };

  const getCategoryBadgeVariant = (category: string): BadgeVariant => {
    switch (category) {
      case 'DOCKER':
      case 'CI_CD':
        return 'info';
      case 'SOURCE_CODE':
        return 'success';
      case 'CONFIG':
        return 'moderate';
      case 'TEST':
        return 'low';
      case 'DOCUMENTATION':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FolderGit2 className="w-6 h-6 text-emerald-400" />
            Repository Loader & RAG Foundation
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Phase 2: Ingestion, AST/Semantic Chunking, Vector Storage (Chroma), and Traceable Knowledge Retrieval
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info">PHASE 2 RAG</Badge>
          <Badge variant="neutral">CHROMA LOCAL</Badge>
        </div>
      </div>

      {/* Grid: Ingestion & Repository State */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Step 1: Ingestion Panel */}
        <div className="lg:col-span-6 space-y-6">
          <Card
            title={
              <span className="flex items-center gap-2">
                <Folder className="w-4 h-4 text-emerald-400" />
                Step 1: Repository Ingestion
              </span>
            }
            subtitle="Load a repository from a local path, GitHub URL, or safe ZIP archive."
          >
            <div className="space-y-4">
              {/* Source Type Selector Tabs */}
              <div className="flex items-center rounded-lg bg-slate-950/80 p-1 border border-slate-800 font-mono text-xs">
                <button
                  type="button"
                  onClick={() => setSourceType('local')}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    sourceType === 'local'
                      ? 'bg-emerald-600 text-white shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Local Directory
                </button>
                <button
                  type="button"
                  onClick={() => setSourceType('github')}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    sourceType === 'github'
                      ? 'bg-emerald-600 text-white shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  GitHub URL
                </button>
                <button
                  type="button"
                  onClick={() => setSourceType('zip')}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    sourceType === 'zip'
                      ? 'bg-emerald-600 text-white shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Upload ZIP
                </button>
              </div>

              {/* Target Input */}
              {sourceType === 'local' && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-slate-300">Filesystem Directory Path</label>
                    <button
                      type="button"
                      onClick={() => setTargetPath('demo-repos/deploysafe-rag-demo')}
                      className="text-[11px] text-emerald-400 hover:text-emerald-300 font-mono underline"
                    >
                      Use Demo Repository
                    </button>
                  </div>
                  <input
                    type="text"
                    value={targetPath}
                    onChange={(e) => setTargetPath(e.target.value)}
                    placeholder="e.g. demo-repos/deploysafe-rag-demo or D:\Projects\my-app"
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                  <p className="text-[11px] text-slate-500">
                    Validated against path traversal, symlink security, and size quotas.
                  </p>
                </div>
              )}

              {sourceType === 'github' && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-slate-300">GitHub Repository URL or Slug</label>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-mono">Presets:</span>
                        <button
                          type="button"
                          onClick={() => setTargetPath('https://github.com/yashrao2607/web-scrape')}
                          className="text-[10px] text-emerald-400 hover:text-emerald-300 font-mono underline"
                        >
                          web-scrape
                        </button>
                        <button
                          type="button"
                          onClick={() => setTargetPath('https://github.com/bottlepy/bottle')}
                          className="text-[10px] text-cyan-400 hover:text-cyan-300 font-mono underline"
                        >
                          bottle
                        </button>
                      </div>
                    </div>
                    <input
                      type="text"
                      value={targetPath}
                      onChange={(e) => setTargetPath(e.target.value)}
                      placeholder="https://github.com/owner/repository or owner/repo"
                      className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-slate-300">Target Branch / Ref</label>
                    <input
                      type="text"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      placeholder="main"
                      className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>
              )}

              {sourceType === 'zip' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">ZIP File (.zip archive)</label>
                  <div className="border border-dashed border-slate-800 rounded-lg p-4 text-center bg-slate-950/60 hover:border-slate-700 transition-colors">
                    <input
                      type="file"
                      accept=".zip"
                      onChange={(e) => setZipFile(e.target.files ? e.target.files[0] : null)}
                      className="block w-full text-xs text-slate-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer"
                    />
                    <p className="text-[11px] text-slate-500 mt-2">
                      Zip-Slip safe extraction with max 200MB size limit and 2000 file ceiling.
                    </p>
                  </div>
                </div>
              )}

              {/* Error Display */}
              {ingestError && (
                <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-md text-xs text-red-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{ingestError}</span>
                </div>
              )}

              <Button
                variant="primary"
                className="w-full text-xs"
                onClick={handleIngest}
                isLoading={isIngesting}
                icon={<UploadCloud className="w-4 h-4" />}
              >
                {isIngesting ? 'Ingesting Snapshot...' : 'Ingest Repository'}
              </Button>
            </div>
          </Card>

          {/* Ingested Snapshot Summary */}
          {snapshot && (
            <Card
              title={
                <div className="flex items-center justify-between w-full">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Snapshot Details: {snapshot.repository_name}
                  </span>
                  <Badge variant="success">INGESTED</Badge>
                </div>
              }
              subtitle="Normalized repository representation stored in DeploySafe workspace."
            >
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2 p-3 bg-slate-950 rounded-md border border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[10px]">REPOSITORY ID</span>
                    <span className="text-slate-200 truncate block">{snapshot.repository_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">SOURCE TYPE</span>
                    <span className="text-emerald-400 uppercase font-bold">{snapshot.source_type}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">DISCOVERED FILES</span>
                    <span className="text-slate-200">{snapshot.file_count} files</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">TOTAL SIZE</span>
                    <span className="text-slate-200">{(snapshot.total_size_bytes / 1024).toFixed(1)} KB</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-500 block text-[10px]">ROOT PATH</span>
                    <span className="text-slate-400 text-[11px] truncate block">{snapshot.root_path}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    onClick={handleStartIndexing}
                    isLoading={isIndexing}
                    icon={<Cpu className="w-3.5 h-3.5" />}
                  >
                    {isIndexing ? 'Indexing & Embedding...' : 'Index & Embed Repository'}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      fetchDiscoveredFiles(snapshot.repository_id);
                      setShowFilesModal(true);
                    }}
                    icon={<FileText className="w-3.5 h-3.5" />}
                  >
                    Files
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      window.location.hash = `#analyze?repo=${encodeURIComponent(snapshot.repository_id)}`;
                      window.dispatchEvent(new CustomEvent('deploysafe-navigate'));
                    }}
                    icon={<Play className="w-3.5 h-3.5 text-emerald-400" />}
                  >
                    Analyze
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Step 2: Indexing State & Metrics */}
        <div className="lg:col-span-6 space-y-6">
          <Card
            title={
              <span className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                Step 2: Real-time Indexing Pipeline
              </span>
            }
            subtitle="Tracks AST chunking, secret redaction, and Chroma vector persistence."
          >
            {indexSummary ? (
              <div className="space-y-4">
                {/* Pipeline State Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Current Pipeline Phase</span>
                    <Badge variant={getStatusBadgeVariant(indexSummary.status)}>
                      {indexSummary.status}
                    </Badge>
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full transition-all duration-500 ${
                        indexSummary.status === 'COMPLETED'
                          ? 'bg-emerald-500 w-full'
                          : indexSummary.status === 'FAILED'
                          ? 'bg-red-500 w-full'
                          : indexSummary.status === 'INDEXING'
                          ? 'bg-cyan-500 w-5/6'
                          : indexSummary.status === 'EMBEDDING'
                          ? 'bg-blue-500 w-4/6'
                          : indexSummary.status === 'CHUNKING'
                          ? 'bg-amber-500 w-3/6'
                          : indexSummary.status === 'DISCOVERING'
                          ? 'bg-purple-500 w-2/6'
                          : 'bg-emerald-600 w-1/6'
                      }`}
                    />
                  </div>
                </div>

                {/* Indexing Metrics Grid */}
                <div className="grid grid-cols-3 gap-3 font-mono text-center">
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                    <span className="text-[10px] text-slate-500 block">FILES INDEXED</span>
                    <span className="text-lg font-bold text-white">
                      {indexSummary.files_indexed} / {indexSummary.files_discovered}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                    <span className="text-[10px] text-slate-500 block">CHUNKS CREATED</span>
                    <span className="text-lg font-bold text-emerald-400">{indexSummary.chunks_created}</span>
                  </div>
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-md">
                    <span className="text-[10px] text-slate-500 block">VECTORS PERSISTED</span>
                    <span className="text-lg font-bold text-cyan-400">{indexSummary.embeddings_created}</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-md font-mono text-xs space-y-1 text-slate-400">
                  <div className="flex justify-between">
                    <span>Duration:</span>
                    <span className="text-slate-200">{indexSummary.duration_seconds}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Files Skipped (non-code / ignored):</span>
                    <span className="text-slate-200">{indexSummary.files_skipped}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Embedding Failures:</span>
                    <span className={indexSummary.embedding_failures > 0 ? 'text-red-400' : 'text-slate-200'}>
                      {indexSummary.embedding_failures}
                    </span>
                  </div>
                  {indexSummary.error_message && (
                    <div className="text-red-400 mt-2 text-[11px] border-t border-red-900/40 pt-1">
                      Error: {indexSummary.error_message}
                    </div>
                  )}
                </div>

                {indexSummary.status === 'COMPLETED' && (
                  <div className="p-2.5 bg-emerald-950/40 border border-emerald-800/60 rounded-md text-xs text-emerald-300 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Repository indexed successfully into Chroma. Ready for semantic RAG queries.</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-10 text-slate-500 font-mono text-xs">
                Ingest a repository snapshot and click &quot;Index &amp; Embed&quot; to inspect real pipeline telemetry.
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Step 3: Semantic Knowledge Retrieval Interface */}
      <Card
        title={
          <div className="flex items-center justify-between w-full">
            <span className="flex items-center gap-2">
              <Search className="w-4 h-4 text-emerald-400" />
              Step 3: Repository Knowledge Retrieval (RAG Evidence Engine)
            </span>
            {searchResponse && (
              <Badge variant={getStatusBadgeVariant(searchResponse.status)}>
                {searchResponse.status} ({searchResponse.results_count} hits)
              </Badge>
            )}
          </div>
        }
        subtitle="Retrieve verifiable repository evidence with exact file paths and source line boundaries. No hallucinated LLM responses."
      >
        <div className="space-y-4">
          {/* Query Bar */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Ask about this repository (e.g. 'Where is Docker deployment configured?')..."
                className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-4 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={() => handleSearch()}
              isLoading={isSearching}
              disabled={!snapshot || indexSummary?.status !== 'COMPLETED'}
              icon={<Search className="w-4 h-4" />}
            >
              Search
            </Button>
          </div>

          {/* Quick Query Suggestions */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
            <span className="text-slate-500">Quick queries:</span>
            {[
              'Where is the Docker deployment configured?',
              'How are tests executed in this project?',
              'Where are database environment variables documented?',
            ].map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setSearchQuery(q);
                  handleSearch(q);
                }}
                disabled={!snapshot || indexSummary?.status !== 'COMPLETED'}
                className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-emerald-400 hover:border-slate-700 transition-colors disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Search Results & Evidence Viewer */}
          {searchResponse && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 pt-4 border-t border-slate-800/80">
              {/* Results List */}
              <div className="lg:col-span-5 space-y-2">
                <div className="text-xs font-mono text-slate-400 flex items-center justify-between pb-1">
                  <span>RETRIEVED CHUNKS</span>
                  <span>{searchResponse.results.length} EVIDENCE ITEMS</span>
                </div>

                {searchResponse.status === 'NOT_FOUND' || searchResponse.results.length === 0 ? (
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-md text-xs font-mono text-slate-400">
                    No sufficiently relevant repository evidence was found for this query. DeploySafe strict RAG does not fabricate imaginary files.
                  </div>
                ) : (
                  searchResponse.results.map((hit) => {
                    const isSelected = selectedEvidence?.chunk_id === hit.chunk_id;
                    return (
                      <div
                        key={hit.chunk_id}
                        onClick={() => setSelectedEvidence(hit)}
                        className={`p-3 rounded-md border cursor-pointer transition-all font-mono text-xs ${
                          isSelected
                            ? 'bg-slate-900/90 border-emerald-500/80 shadow-sm'
                            : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900/40'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="font-semibold text-slate-200 truncate flex items-center gap-1.5">
                            <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            {hit.file_path}
                          </span>
                          <span className="text-[11px] text-emerald-400 font-bold shrink-0">
                            {Math.round(hit.relevance_score * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>
                            Lines {hit.line_start}–{hit.line_end}
                          </span>
                          <Badge variant={getCategoryBadgeVariant(hit.category)}>{hit.category}</Badge>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Code Evidence Viewer */}
              <div className="lg:col-span-7">
                {selectedEvidence ? (
                  <div className="rounded-md border border-slate-800 bg-slate-950 overflow-hidden font-mono text-xs">
                    {/* Evidence Header */}
                    <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
                      <div className="flex items-center gap-2 truncate">
                        <Terminal className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="font-bold text-slate-200">{selectedEvidence.file_path}</span>
                        <span className="text-slate-500">
                          (Lines {selectedEvidence.line_start}–{selectedEvidence.line_end})
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            handleCopyCode(selectedEvidence.chunk_id, selectedEvidence.content)
                          }
                          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex items-center gap-1 text-[11px]"
                        >
                          {copiedChunkId === selectedEvidence.chunk_id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" /> Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" /> Copy
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Metadata Summary */}
                    <div className="px-4 py-2 bg-slate-900/40 border-b border-slate-800/80 flex items-center gap-4 text-[11px] text-slate-400">
                      <span>
                        Category: <strong className="text-slate-300">{selectedEvidence.category}</strong>
                      </span>
                      <span>
                        Language: <strong className="text-slate-300">{selectedEvidence.language}</strong>
                      </span>
                      <span>
                        Relevance:{' '}
                        <strong className="text-emerald-400">
                          {(selectedEvidence.relevance_score * 100).toFixed(1)}%
                        </strong>
                      </span>
                    </div>

                    {/* Code Snippet with Line Numbers */}
                    <div className="p-4 overflow-x-auto max-h-[380px] bg-slate-950">
                      <pre className="text-slate-200 leading-relaxed font-mono">
                        {selectedEvidence.content.split('\n').map((line, idx) => (
                          <div key={idx} className="flex">
                            <span className="w-10 select-none text-slate-600 text-right pr-4 shrink-0">
                              {selectedEvidence.line_start + idx}
                            </span>
                            <span className="whitespace-pre">{line}</span>
                          </div>
                        ))}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="h-full min-h-[220px] rounded-md border border-dashed border-slate-800 flex items-center justify-center text-xs font-mono text-slate-500">
                    Select a retrieved evidence chunk to inspect traceable source code and line numbers.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Discovered Files Modal / Drawer */}
      {showFilesModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  Discovered Repository Files ({discoveredFiles.length})
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Classified into categories with ignore rules, binary detection, and path validation applied.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowFilesModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-2 flex-1">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-[10px]">
                    <th className="pb-2">FILE PATH</th>
                    <th className="pb-2">CATEGORY</th>
                    <th className="pb-2">LANGUAGE</th>
                    <th className="pb-2 text-right">SIZE</th>
                    <th className="pb-2 text-center">INDEXABLE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {discoveredFiles.map((f, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-2.5 text-slate-200 font-semibold">{f.path}</td>
                      <td className="py-2.5">
                        <Badge variant={getCategoryBadgeVariant(f.category)}>{f.category}</Badge>
                      </td>
                      <td className="py-2.5 text-slate-400">{f.language}</td>
                      <td className="py-2.5 text-right text-slate-400">{f.size_bytes} B</td>
                      <td className="py-2.5 text-center">
                        {f.is_indexable ? (
                          <Badge variant="success">INDEXABLE</Badge>
                        ) : (
                          <Badge variant="critical">SKIPPED</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="px-6 py-3 border-t border-slate-800 text-right">
              <Button variant="secondary" size="sm" onClick={() => setShowFilesModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
