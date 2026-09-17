import type { Article } from "@/lib/types";
import { sgtTime } from "@/lib/format";

const TOPIC: Record<string, string> = {
  fed: "Fed", rates: "Rates", inflation: "Inflation", oil: "Oil", equities: "Equities",
};

export default function NewsList({ articles }: { articles: Article[] }) {
  if (!articles.length) {
    return <p className="quiet">No macro headlines in the last 48 hours. They refresh with each update run.</p>;
  }
  return (
    <ul className="news">
      {articles.map((a) => (
        <li key={a.url}>
          <a href={a.url} target="_blank" rel="noopener noreferrer">
            <span className="news-title">{a.title}</span>
          </a>
          <div className="news-meta">
            <span className="topic">{TOPIC[a.topic ?? ""] ?? "Markets"}</span>
            <span>{a.domain}</span>
            <span>{sgtTime(a.published_at)}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
