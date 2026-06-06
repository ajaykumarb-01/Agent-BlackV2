type Status = "online" | "offline" | "warning";

export function StatusDot({ status = "online", className = "" }: { status?: Status; className?: string }) {
  const color =
    status === "online" ? "bg-success" : status === "warning" ? "bg-warning" : "bg-error";
  return (
    <span className={`relative inline-flex h-2 w-2 ${className}`}>
      <span className={`absolute inline-flex h-full w-full rounded-full ${color} opacity-60 animate-ping`} />
      <span className={`relative inline-flex h-2 w-2 rounded-full ${color}`} />
    </span>
  );
}
