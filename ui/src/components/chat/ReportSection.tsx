import ReactMarkdown from "react-markdown";
import { Collapsible } from "@/components/shared/Collapsible";
import type { ReportSections } from "@/lib/store";

const titles: Record<keyof ReportSections, string> = {
  literature_review: "Literature Review",
  datasets: "Datasets",
  models: "Models",
  evaluation_plan: "Evaluation Plan",
  prototype_guidance: "Prototype Guidance",
};

export function ReportSections({ sections }: { sections: ReportSections }) {
  const keys = Object.keys(titles) as (keyof ReportSections)[];
  return (
    <div className="flex flex-col gap-2">
      {keys.map((k, i) => {
        const raw = sections[k];
        const content = typeof raw === "string" ? raw : raw ? JSON.stringify(raw, null, 2) : null;
        return (
          <Collapsible key={k} title={titles[k]} defaultOpen={i === 0}>
            {content ? (
              <div className="md-body">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm text-text-muted italic">
                Not applicable for this query
              </p>
            )}
          </Collapsible>
        );
      })}
    </div>
  );
}
