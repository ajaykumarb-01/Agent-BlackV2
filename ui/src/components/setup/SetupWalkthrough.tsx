import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { Loader2, Check } from "lucide-react";

interface SetupProps {
  onComplete: () => void;
}

export function SetupWalkthrough({ onComplete }: SetupProps) {
  const [step, setStep] = useState(0);
  const [provider, setProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gemini-1.5-flash");
  const [baseUrl, setBaseUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.setupStatus().then((s) => {
      if (s.complete) {
        onComplete();
        return;
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const steps = [
    {
      title: "Welcome to Agent Black",
      description: "This walkthrough will guide you through setting up the system. You'll configure an LLM provider and agent URLs.",
      action: "Get Started",
    },
    {
      title: "Choose an LLM Provider",
      description: "Select your preferred language model provider and enter your API key.",
      content: (
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-text-muted">Provider</span>
            <select
              value={provider}
              onChange={(e) => {
                const p = e.target.value;
                setProvider(p);
                setBaseUrl("");
                if (p === "gemini") setModel("gemini-1.5-flash");
                else if (p === "openai") setModel("gpt-4o");
                else if (p === "anthropic") setModel("claude-3-5-sonnet-20241022");
              }}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
            >
              <option value="gemini">Gemini (Google)</option>
              <option value="openai">OpenAI (or compatible)</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-text-muted">Model</span>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
              placeholder="gemini-1.5-flash"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-text-muted">API Key</span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
              placeholder="Enter your API key..."
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] uppercase tracking-wider text-text-muted">Base URL (optional)</span>
            <input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-foreground/40"
              placeholder={provider === "openai" ? "https://api.openai.com/v1" : "Custom endpoint URL"}
            />
          </label>
        </div>
      ),
      action: "Next",
    },
    {
      title: "Agent URLs (Optional)",
      description: "Configure the URLs for each specialized agent. These defaults work for local development.",
      content: (
        <div className="flex flex-col gap-3">
          <p className="text-xs text-text-secondary">
            The agents run on ports 8001–8003 by default. Change these if you're using Docker or a different setup.
          </p>
          <div className="rounded-lg border border-border bg-background p-3 text-xs font-mono text-text-secondary">
            <div>Research Agent → http://localhost:8001</div>
            <div>Solution Agent → http://localhost:8002</div>
            <div>Experiment Agent → http://localhost:8003</div>
          </div>
        </div>
      ),
      action: "Complete Setup",
    },
  ];

  const handleNext = async () => {
    if (step < steps.length - 1) {
      setError("");
      try {
        await api.completeSetupStep(step === 0 ? "welcome" : step === 1 ? "llm_provider" : "agent_urls");
        setStep(step + 1);
      } catch (err: any) {
        setError(err.message || "Failed to advance step");
      }
      return;
    }
    if (!apiKey && provider !== "none") {
      setError("API key is required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api.completeSetup({
        llm_provider: provider,
        api_key: apiKey,
        model,
        base_url: baseUrl || undefined,
      });
      await api.completeSetupStep("complete");
      useAppStore.getState().setProvider(provider as "gemini" | "openai" | "anthropic");
      onComplete();
    } catch (err: any) {
      setError(err.message || "Failed to complete setup");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
        <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
      </div>
    );
  }

  const current = steps[step];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-surface shadow-xl p-8">
        <div className="mb-8 flex items-center gap-2">
          {steps.map((_, i) => (
            <div key={i} className="flex items-center gap-2 flex-1">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                  i <= step
                    ? "bg-foreground text-background"
                    : "border border-border text-text-muted"
                }`}
              >
                {i < step ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              {i < steps.length - 1 && (
                <div className={`h-px flex-1 ${i < step ? "bg-foreground" : "bg-border"}`} />
              )}
            </div>
          ))}
        </div>

        <h2 className="text-xl font-semibold tracking-tight">{current.title}</h2>
        <p className="mt-2 text-sm text-text-secondary">{current.description}</p>

        {current.content && <div className="mt-6">{current.content}</div>}

        {error && (
          <div className="mt-4 rounded-lg border border-error/30 bg-error/5 px-4 py-2 text-xs text-error">
            {error}
          </div>
        )}

        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={() => {
              if (step > 0) setStep(step - 1);
            }}
            className={`text-sm text-text-secondary hover:text-foreground transition-colors ${
              step === 0 ? "invisible" : ""
            }`}
          >
            Back
          </button>
          <button
            onClick={handleNext}
            disabled={saving || (step === 1 && !apiKey)}
            className="rounded-lg bg-foreground px-5 py-2 text-sm text-background hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {saving ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving...
              </span>
            ) : (
              current.action
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
