import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type HistoryItem } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export const Route = createFileRoute("/history")({
  head: () => ({ meta: [      { title: "History · Agent Black" }] }),
  component: HistoryPage,
});

function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const clearMessages = useAppStore((s) => s.clearMessages);

  const fetchHistory = () => {
    api.queryHistory().then((data) => {
      setItems(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleClear = async () => {
    await api.clearHistory();
    clearMessages();
    setItems([]);
  };

  const filtered = items.filter((i) =>
    i.query.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="mx-auto w-full max-w-[860px] px-4 py-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">History</h1>
        {items.length > 0 && (
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs hover:bg-surface-hover"
          >
            <Trash2 className="h-3.5 w-3.5" /> Clear all
          </button>
        )}
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search past queries…"
          className="w-full rounded-lg border border-border bg-surface py-2.5 pl-10 pr-3 text-sm outline-none focus:border-foreground/40"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-sm text-text-muted">
          Loading history...
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-surface/50 p-12 text-center text-sm text-text-secondary">
          {items.length === 0
            ? "No queries yet. Start a conversation on the Chat page."
            : "No results match your search."}
        </div>
      ) : (
        <ul className="rounded-xl border border-border bg-surface divide-y divide-border-light">
          {filtered.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer hover:bg-surface-hover transition-colors"
              onClick={() => navigate({ to: "/" })}
            >
              <span className="truncate text-sm">{item.query}</span>
              <span className="text-xs text-text-muted whitespace-nowrap">
                {new Date(item.created_at * 1000).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
