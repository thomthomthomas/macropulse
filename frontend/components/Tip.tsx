export default function Tip({ text, label }: { text: string; label: string }) {
  return (
    <button type="button" className="tip" aria-label={`About ${label}`}>
      ?
      <span className="tip-body" role="tooltip">{text}</span>
    </button>
  );
}
