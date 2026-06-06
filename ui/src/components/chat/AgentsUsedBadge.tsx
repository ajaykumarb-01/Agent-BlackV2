const map: Record<string, string> = {
  research: "Research",
  solution: "Solution",
  experiment: "Experiment",
  CV: "CV",
  NLP: "NLP",
  ML: "ML",
};

export function AgentsUsedBadge({ agents }: { agents?: string[] }) {
  if (!agents || agents.length === 0) return null;
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-text-secondary">
      <span className="h-1.5 w-1.5 rounded-full bg-foreground" />
      <span>Agents:</span>
      <span className="text-foreground">
        {agents.map((a) => map[a] ?? a).join(" + ")}
      </span>
    </div>
  );
}
