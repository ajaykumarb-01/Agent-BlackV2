import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";
import { useDarkMode } from "@/hooks/use-dark-mode";
import { api, type SettingsResponse, type AgentNetworkConfig } from "@/lib/api";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · Agent Black" }] }),
  component: SettingsPage,
});

const AGENT_KEYS = ["research", "solution", "experiment"] as const;
type AgentMode = "local" | "network" | "disabled";
const MODE_CYCLE: AgentMode[] = ["local", "network", "disabled"];

const MODE_STYLES: Record<AgentMode, { bg: string; label: string; dot: string }> = {
  local: { bg: "bg-green-500", label: "LOCAL", dot: "bg-green-400" },
  network: { bg: "bg-blue-500", label: "NETWORK", dot: "bg-blue-400" },
  disabled: { bg: "bg-red-500", label: "DISABLED", dot: "bg-red-400" },
};

function SettingsPage() {
  const provider = useAppStore((s) => s.provider);
  const setProvider = useAppStore((s) => s.setProvider);
  const { darkMode, setDarkMode } = useDarkMode();

  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [kaggleUsername, setKaggleUsername] = useState("");
  const [kaggleKey, setKaggleKey] = useState("");
  const [agentNetwork, setAgentNetwork] = useState<
    Record<string, AgentNetworkConfig>
  >({
    research: { mode: "local", network_host: "", network_port: 8001 },
    solution: { mode: "local", network_host: "", network_port: 8002 },
    experiment: { mode: "local", network_host: "", network_port: 8003 },
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [agentSaving, setAgentSaving] = useState(false);
  const [agentMsg, setAgentMsg] = useState("");

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        setProvider(s.llm_provider as "gemini" | "openai" | "anthropic");
        const cur = s.providers[s.llm_provider];
        setModel(cur?.model || "");
        setBaseUrl(cur?.base_url || "");
        setKaggleUsername(s.kaggle_username || "");
        if (s.agent_network) {
          setAgentNetwork((prev) => {
            const next = { ...prev };
            for (const key of AGENT_KEYS) {
              const cfg = s.agent_network[key];
              if (cfg) {
                next[key] = cfg;
              }
            }
            return next;
          });
        }
      })
      .catch(() => {});
  }, []);

  const cycleMode = (key: string) => {
    setAgentNetwork((prev) => {
      const cur = prev[key].mode;
      const idx = MODE_CYCLE.indexOf(cur);
      const nextMode = MODE_CYCLE[(idx + 1) % MODE_CYCLE.length];
      return { ...prev, [key]: { ...prev[key], mode: nextMode } };
    });
  };

  const updateNetworkHost = (key: string, host: string) => {
    setAgentNetwork((prev) => ({
      ...prev,
      [key]: { ...prev[key], network_host: host },
    }));
  };

  const updateNetworkPort = (key: string, port: string) => {
    const num = parseInt(port, 10);
    setAgentNetwork((prev) => ({
      ...prev,
      [key]: { ...prev[key], network_port: isNaN(num) ? 0 : num },
    }));
  };

  const handleSaveAgentNetwork = async () => {
    setAgentSaving(true);
    setAgentMsg("");
    try {
      const payload: Record<string, any> = { agent_network: {} };
      for (const key of AGENT_KEYS) {
        const cfg = agentNetwork[key];
        payload.agent_network[key] = {
          mode: cfg.mode,
          network_host: cfg.network_host,
          network_port: cfg.network_port,
        };
      }
      await api.updateSettings(payload);
      setAgentMsg("Agent configuration saved");
    } catch (err: any) {
      setAgentMsg(`Error: ${err.message}`);
    } finally {
      setAgentSaving(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMsg("");
    try {
      const payload: Record<string, any> = { llm_provider: provider };
      if (apiKey) payload[`${provider}_api_key`] = apiKey;
      if (baseUrl) payload[`${provider}_base_url`] = baseUrl;
      if (model) payload[`${provider}_model`] = model;
      payload.kaggle_username = kaggleUsername || undefined;
      if (kaggleKey) payload.kaggle_key = kaggleKey;
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
    <div className="mx-auto w-full max-w-[720px] px-3 py-4 sm:px-4 sm:py-6 flex flex-col gap-6">
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

      <Section title="Agent Network Configuration">
        <p className="text-xs text-text-secondary">
          Click the button to cycle through modes:{" "}
          <span className="text-green-400 font-medium">Local</span> (runs here) →{" "}
          <span className="text-blue-400 font-medium">Network</span> (remote PC) →{" "}
          <span className="text-red-400 font-medium">Disabled</span> (not used).
          Network agents must be running on the remote host independently.
        </p>
        {AGENT_KEYS.map((key) => {
          const cfg = agentNetwork[key];
          const mode = cfg.mode;
          const styles = MODE_STYLES[mode];
          const label = key.charAt(0).toUpperCase() + key.slice(1);
          return (
            <div key={key} className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => cycleMode(key)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${styles.bg}`}
                  title={`Click to change: current = ${styles.label}`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${
                      mode === "disabled"
                        ? "translate-x-0"
                        : mode === "network"
                          ? "translate-x-5"
                          : "translate-x-5"
                    }`}
                  />
                </button>
                <span className="text-sm font-medium">{label} Agent</span>
                <span
                  className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${styles.bg}/20 ${styles.dot}`}
                >
                  {styles.label}
                </span>
              </div>
              {mode === "network" && (
                <div className="flex gap-2 ml-14">
                  <div className="flex-1">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted">
                      Host / IP
                    </span>
                    <Input
                      value={cfg.network_host}
                      onChange={(v) => updateNetworkHost(key, v)}
                      placeholder="192.168.1.101"
                    />
                  </div>
                  <div className="w-24">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted">
                      Port
                    </span>
                    <Input
                      value={String(cfg.network_port)}
                      onChange={(v) => updateNetworkPort(key, v)}
                      placeholder="8001"
                    />
                  </div>
                </div>
              )}
              {mode === "disabled" && (
                <p className="ml-14 text-[11px] text-red-400/70">
                  This agent will not be discovered or used by the orchestrator.
                </p>
              )}
            </div>
          );
        })}
        <div className="flex items-center gap-3 mt-2">
          <button
            onClick={handleSaveAgentNetwork}
            disabled={agentSaving}
            className="self-start rounded-md bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-90 disabled:opacity-50"
          >
            {agentSaving ? "Saving..." : "Save Agent Config"}
          </button>
          {agentMsg && <span className="text-xs text-text-secondary">{agentMsg}</span>}
        </div>
      </Section>

      <Section title="Kaggle API">
        <p className="text-xs text-text-secondary">
          Required to fetch live datasets from Kaggle. Get your credentials from{" "}
          <a
            href="https://www.kaggle.com/settings"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            kaggle.com/settings
          </a>{" "}
          (API section → Create New Token).
        </p>
        <Field label="Kaggle Username">
          <Input value={kaggleUsername} onChange={setKaggleUsername} placeholder="yourusername" />
        </Field>
        <Field label="Kaggle API Key">
          <Input
            value={kaggleKey}
            onChange={setKaggleKey}
            placeholder={
              settings?.kaggle_key_set
                ? "Key already set (type to replace)"
                : "Paste your kaggle.json key..."
            }
            type="password"
          />
        </Field>
      </Section>

      <Section title="Theme">
        <div className="flex flex-wrap gap-2">
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
    <div className="rounded-xl border border-border bg-surface p-4 flex flex-col gap-4 sm:p-5">
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
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
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
