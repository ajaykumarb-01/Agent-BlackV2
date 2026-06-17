import { ArrowUp, Settings2, Sparkles } from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";

export function InputArea({
  onSubmit,
  disabled,
  placeholder,
}: {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
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
    <div className="sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent pt-6 pb-4">
      <div className="mx-auto max-w-[860px] px-4">
        <div
          className={`flex items-end gap-2 rounded-2xl border bg-surface p-2 transition-[border-color,box-shadow] duration-200 ${
            focused
              ? "border-foreground/30 shadow-lg shadow-foreground/5"
              : "border-border shadow-sm"
          } sm:p-2.5`}
        >
          <button
            type="button"
            className="rounded-xl p-2.5 text-text-secondary hover:bg-surface-hover hover:text-foreground transition-colors"
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
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            rows={1}
            placeholder={placeholder || "Ask the agents to research, design, or prototype..."}
            className="flex-1 resize-none bg-transparent px-2 py-2.5 text-sm leading-6 outline-none placeholder:text-text-muted sm:text-[15px]"
          />
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className={`inline-flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-200 ${
              value.trim() && !disabled
                ? "bg-foreground text-background shadow-sm hover:opacity-90 hover:shadow-md"
                : "bg-surface-hover text-text-muted"
            }`}
            aria-label="Send"
          >
            {value.trim() ? (
              <ArrowUp className="h-4 w-4" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
          </button>
        </div>
        <p className="mt-2.5 hidden text-center text-[11px] text-text-muted sm:block">
          Enter to send · Shift + Enter for newline
        </p>
      </div>
    </div>
  );
}
