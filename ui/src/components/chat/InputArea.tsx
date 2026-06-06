import { ArrowUp, Settings2 } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";

export function InputArea({
  onSubmit,
  disabled,
}: {
  onSubmit: (text: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const resize = () => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSubmit(text);
    setValue("");
    requestAnimationFrame(resize);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent pt-4 pb-4">
      <div className="mx-auto max-w-[860px] px-4">
        <div className="flex items-end gap-2 rounded-2xl border border-border bg-surface p-2 shadow-sm focus-within:border-foreground/40 transition-colors">
          <button
            type="button"
            className="rounded-lg p-2 text-text-secondary hover:bg-surface-hover"
            aria-label="Tech stack settings"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              resize();
            }}
            onKeyDown={onKey}
            rows={1}
            placeholder="Ask the agents to research, design, or prototype…"
            className="flex-1 resize-none bg-transparent px-1 py-2 text-[15px] leading-6 outline-none placeholder:text-text-muted"
          />
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-foreground text-background transition-opacity hover:opacity-90 disabled:opacity-30"
            aria-label="Send"
          >
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-text-muted">
          Enter to send · Shift + Enter for newline
        </p>
      </div>
    </div>
  );
}
