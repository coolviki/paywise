import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  Copy,
  Check,
  KeyRound,
  Trash2,
  ShieldCheck,
  Smartphone,
  AlertTriangle,
  X,
  MessageSquare,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { mcpKeyService, MCP_CONNECTOR_URL } from '../services/mcpKeyService';
import { McpKey, McpKeyCreated } from '../types';

const EXAMPLE_PROMPTS = [
  'Dinner for 6 at a Taj property tonight, about ₹12,000. Which card?',
  'Buying a ₹65k laptop at Croma — any bank offers on my cards?',
  'Which of my cards is best for BigBasket groceries?',
];

function timeAgo(iso?: string | null): string {
  if (!iso) return 'Never used';
  const then = new Date(iso.endsWith('Z') ? iso : `${iso}Z`).getTime();
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (mins < 1) return 'Used just now';
  if (mins < 60) return `Used ${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `Used ${hrs} hr ago`;
  return `Used ${Math.round(hrs / 24)} days ago`;
}

function formatDate(iso: string): string {
  return new Date(iso.endsWith('Z') ? iso : `${iso}Z`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function CopyButton({ value, label = 'Copy' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable - user can still select the text */
    }
  };
  return (
    <button
      onClick={onCopy}
      className="shrink-0 inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg bg-primary-50 text-primary-600 hover:bg-primary-100 dark:bg-primary-900/30 dark:text-primary-300"
    >
      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      {copied ? 'Copied' : label}
    </button>
  );
}

function StepBadge({ n }: { n: number }) {
  return (
    <span className="w-6 h-6 shrink-0 rounded-full bg-primary-500 text-white text-xs font-semibold flex items-center justify-center">
      {n}
    </span>
  );
}

export function ConnectClaude() {
  const navigate = useNavigate();
  const [keys, setKeys] = useState<McpKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [keyName, setKeyName] = useState('Claude');
  const [newKey, setNewKey] = useState<McpKeyCreated | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setKeys(await mcpKeyService.list());
    } catch {
      setError('Could not load your keys. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const created = await mcpKeyService.create(keyName.trim() || 'Claude');
      setNewKey(created);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not create a key.');
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (key: McpKey) => {
    if (!window.confirm(`Revoke "${key.name}"? Claude will stop working with this key immediately.`)) return;
    await mcpKeyService.revoke(key.id);
    await load();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Connect to Claude</h1>
        </div>
      </div>

      <div className="p-4 space-y-6 max-w-2xl mx-auto">
        {/* Intro */}
        <Card className="p-5 bg-gradient-to-br from-primary-50 to-white dark:from-primary-900/20 dark:to-gray-800">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-primary-500 text-white">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">
                Ask Claude which card to use
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                Connect PayWise to Claude once, then just ask in the Claude app — on your phone, at the
                counter. Claude checks your saved cards and live offers and tells you the best card.
              </p>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {EXAMPLE_PROMPTS.map((p) => (
              <div
                key={p}
                className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-200 bg-white/80 dark:bg-gray-700/60 rounded-lg px-3 py-2"
              >
                <MessageSquare className="w-4 h-4 mt-0.5 text-primary-500 shrink-0" />
                <span>“{p}”</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Step 1 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">Set up (2 minutes)</h2>
          <Card className="divide-y divide-gray-100 dark:divide-gray-700">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <StepBadge n={1} />
                <span className="font-medium text-gray-900 dark:text-white">Copy your connector URL</span>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 min-w-0 truncate text-sm bg-gray-100 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2">
                  {MCP_CONNECTOR_URL}
                </code>
                <CopyButton value={MCP_CONNECTOR_URL} />
              </div>
            </div>

            {/* Step 2 */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <StepBadge n={2} />
                <span className="font-medium text-gray-900 dark:text-white">Generate a personal key</span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                The key tells PayWise it's you. Claude will only ever see <b>your</b> cards.
              </p>
              <div className="flex gap-2">
                <input
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  maxLength={100}
                  placeholder="Key name, e.g. My iPhone"
                  className="flex-1 min-w-0 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <Button
                  size="sm"
                  onClick={handleCreate}
                  isLoading={creating}
                  leftIcon={!creating ? <KeyRound className="w-4 h-4" /> : undefined}
                >
                  Generate
                </Button>
              </div>
              {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
            </div>

            {/* Step 3 */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <StepBadge n={3} />
                <span className="font-medium text-gray-900 dark:text-white">Add it in Claude</span>
              </div>
              <ol className="text-sm text-gray-600 dark:text-gray-300 space-y-1.5 list-decimal pl-5">
                <li>
                  On <b>claude.ai</b> (web or desktop), open <b>Settings → Connectors</b>
                </li>
                <li>
                  Click <b>Add custom connector</b>, name it <b>PayWise</b> and paste the URL
                </li>
                <li>
                  Under <b>Request headers</b>, add <code className="text-xs">Authorization</code> with
                  value <code className="text-xs">Bearer &lt;your key&gt;</code>
                </li>
                <li>Click <b>Add</b> — done</li>
              </ol>
              <div className="flex items-center gap-2 mt-3 text-xs text-gray-500 dark:text-gray-400">
                <Smartphone className="w-4 h-4" />
                Add it once on the web; it then works in the Claude mobile app too.
              </div>
            </div>
          </Card>
        </section>

        {/* Keys */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">Your keys</h2>
          <Card>
            {loading ? (
              <div className="p-6">
                <Loading size="sm" />
              </div>
            ) : keys.length === 0 ? (
              <p className="p-4 text-sm text-gray-500 dark:text-gray-400">
                No keys yet. Generate one above to connect Claude.
              </p>
            ) : (
              keys.map((k, i) => (
                <div
                  key={k.id}
                  className={`flex items-center justify-between p-4 ${
                    i < keys.length - 1 ? 'border-b border-gray-100 dark:border-gray-700' : ''
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300">
                      <KeyRound className="w-4 h-4" />
                    </span>
                    <div className="min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white truncate">{k.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        <code>{k.key_prefix}…</code> · Created {formatDate(k.created_at)} ·{' '}
                        <span className={k.last_used_at ? 'text-accent-500' : ''}>{timeAgo(k.last_used_at)}</span>
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRevoke(k)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    title="Revoke key"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </Card>
        </section>

        {/* Privacy */}
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-accent-500 shrink-0 mt-0.5" />
            <div className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
              <p className="font-medium text-gray-900 dark:text-white">What Claude can see</p>
              <p>Read-only: your saved card names, reward rates and current offers. Claude can't add, edit or remove cards.</p>
              <p>PayWise never stores card numbers, so Claude never sees them. Revoke a key anytime to disconnect.</p>
            </div>
          </div>
        </Card>
      </div>

      {/* One-time key modal */}
      {newKey && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end sm:items-center justify-center p-4">
          <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">Your new key</h3>
              <button onClick={() => setNewKey(null)} className="p-1 text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm mb-4">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              Copy it now — for your security we won't show it again.
            </div>
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Header name</label>
            <div className="flex items-center gap-2 mb-3 mt-1">
              <code className="flex-1 text-sm bg-gray-100 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2">
                Authorization
              </code>
              <CopyButton value="Authorization" />
            </div>
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Header value</label>
            <div className="flex items-center gap-2 mt-1">
              <code className="flex-1 min-w-0 break-all text-sm bg-gray-100 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2">
                Bearer {newKey.api_key}
              </code>
              <CopyButton value={`Bearer ${newKey.api_key}`} />
            </div>
            <Button className="w-full mt-5" onClick={() => setNewKey(null)}>
              I've copied it
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
