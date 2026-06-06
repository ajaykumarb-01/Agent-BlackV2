import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";
import { useDarkMode } from "@/hooks/use-dark-mode";
import { api, type SettingsResponse } from "@/lib/api";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [      { title: "Settings · Agent Black" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  const provider = useAppStore((s) => s.provider);
  const setProvider = useAppStore((s) => s.setProvider);
  const { darkMode, setDarkMode } = useDarkMode();

  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [urls, setUrls] = useState({
    research: "http://localhost:8001",
    solution: "http://localhost:8002",
    experiment: "http://localhost:8003",
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s);
      setProvider(s.llm_provider as "gemini" | "openai" | "anthropic");
      const cur = s.providers[s.llm_provider];
      setModel(cur?.model || "");
      setBaseUrl(cur?.base_url || "");
      setUrls({
        research: s.agent_urls.research || "http://localhost:8001",
        solution: s.agent_urls.solution || "http://localhost:8002",
        experiment: s.agent_urls.experiment || "http://localhost:8003",
      });
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMsg("");
    try {
      const payload: Record<string, any> = { llm_provider: provider };
      if (apiKey) payload[`${provider}_api_key`] = apiKey;
      if (baseUrl) payload[`${provider}_base_url`] = baseUrl;
      if (model) payload[`${provider}_model`] = model;
      payload.research_agent_url = urls.research;
      payload.solution_agent_url = urls.solution;
      payload.experiment_agent_url = urls.experiment;
      await api.updateSettings(payload);
      setMsg("Settings saved successfully");
      setApiKey("");
    } catch (err: any) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-6 flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Settings</h1>

      <Section title="LLM Provider">
        <Field label="Provider">
          <select
            value={provider}
            onChange={(e) => {
              const val = e.target.value as typeof provider;
              setProvider(val);
              if (settings) {
                const p = settings.providers[val];
                setModel(p?.model || "");
                setBaseUrl(p?.base_url || "");
              }
            }}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
          >
            <option value="gemini">Gemini</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </Field>
        <Field label="Model">
          <Input value={model} onChange={setModel} placeholder="gemini-2.0-flash" />
        </Field>
        <Field label="Base URL (optional)">
          <Input value={baseUrl} onChange={setBaseUrl} placeholder="https://api.openai.com/v1" />
        </Field>
        <Field label="API Key">
          <Input
            value={apiKey}
            onChange={setApiKey}
            placeholder={
              settings?.providers[provider]?.api_key_set
                ? "Key already set (type to replace)"
                : "Enter API key..."
            }
            type="password"
          />
        </Field>
        <button
          onClick={handleSave}
          disabled={saving}
          className="self-start rounded-md bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-90 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
        {msg && <span className="text-xs text-text-secondary">{msg}</span>}
      </Section>

      <Section title="Agent URLs">
        {(["research", "solution", "experiment"] as const).map((k) => (
          <Field key={k} label={`${k[0].toUpperCase() + k.slice(1)} Agent`}>
            <Input value={urls[k]} onChange={(v) => setUrls({ ...urls, [k]: v })} />
          </Field>
        ))}
      </Section>

      <Section title="Theme">
        <div className="flex gap-2">
          {(
            [
              { v: null, label: "System" },
              { v: false, label: "Light" },
              { v: true, label: "Dark" },
            ] as const
          ).map((opt) => (
            <button
              key={String(opt.v)}
              onClick={() => setDarkMode(opt.v)}
              className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                darkMode === opt.v
                  ? "border-foreground bg-foreground text-background"
                  : "border-border hover:bg-surface-hover"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 flex flex-col gap-4">
      <h2 className="text-sm font-semibold">{title}</h2>
      {children}
    </div>
  );
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] uppercase tracking-wider text-text-muted">{label}</span>
      {children}
    </label>
  );
}
function Input({
  value, onChange, placeholder, type = "text",
}: { value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
    />
  );
}
