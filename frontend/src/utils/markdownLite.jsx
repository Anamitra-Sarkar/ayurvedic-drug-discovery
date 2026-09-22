/**
 * markdownLite.jsx — small, dependency-free renderer for the plain markdown
 * the real Groq LLM answers come back in (headers, bold/italic, bullet and
 * numbered lists, horizontal rules). No npm markdown library was added on
 * purpose (avoids an untested remote-build risk); this covers exactly the
 * patterns real answers have used, not arbitrary markdown.
 */

/** Inline bold and italic markers within one line of text. */
function renderInline(text, keyPrefix) {
  const parts = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|_(.+?)_/g;
  let lastIndex = 0;
  let m;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) parts.push(text.slice(lastIndex, m.index));
    if (m[1] !== undefined) parts.push(<strong key={`${keyPrefix}-${key++}`}>{m[1]}</strong>);
    else parts.push(<em key={`${keyPrefix}-${key++}`}>{m[2] ?? m[3]}</em>);
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length ? parts : text;
}

/** Strip the trailing boilerplate the UI already shows via its own
 * disclaimer note, evidence-tier badge and real citation list - keeps the
 * real synthesis content (including things like a genuine "Limitations"
 * section) intact. */
export function stripAnswerBoilerplate(raw) {
  if (!raw) return raw;
  let text = raw.replace(/^\*\*Answer:?\*\*\s*/i, '').replace(/^#{1,6}\s*Answer:?\s*/i, '');
  text = text.split(/\n\s*(?:\*\*|#{1,6}\s*)?(?:Disclaimer|Evidence tier)\s*:?\**\s*\n/i)[0];
  text = text.split(/\n\s*(?:---\s*\n\s*)?#{0,6}\s*References\b/i)[0];
  text = text.replace(/\[SAFETY DISCLAIMER\][\s\S]*$/i, '');
  return text.trim();
}

/** Parse plain markdown lines into block objects (heading/ul/ol/p/hr). */
function parseBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let currentList = null;
  const flush = () => { if (currentList) { blocks.push(currentList); currentList = null; } };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) { flush(); continue; }
    if (/^-{3,}$/.test(line)) { flush(); blocks.push({ type: 'hr' }); continue; }
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const numbered = line.match(/^\d+\.\s+(.*)$/);
    if (heading) {
      flush();
      blocks.push({ type: 'heading', level: heading[1].length, text: heading[2] });
    } else if (bullet) {
      if (!currentList || currentList.type !== 'ul') { flush(); currentList = { type: 'ul', items: [] }; }
      currentList.items.push(bullet[1]);
    } else if (numbered) {
      if (!currentList || currentList.type !== 'ol') { flush(); currentList = { type: 'ol', items: [] }; }
      currentList.items.push(numbered[1]);
    } else {
      flush();
      blocks.push({ type: 'p', text: line });
    }
  }
  flush();
  return blocks;
}

/** Render real (already-boilerplate-stripped) markdown prose as proper
 * headings/lists/paragraphs instead of a wall of text with raw syntax. */
export default function MarkdownLite({ text, className = '' }) {
  if (!text) return null;
  const blocks = parseBlocks(text);
  return (
    <div className={className}>
      {blocks.map((b, i) => {
        if (b.type === 'hr') return <hr key={i} className="my-3 border-forest-900/10 dark:border-white/10" />;
        if (b.type === 'heading') {
          return (
            <div key={i} className="mt-3 mb-1 text-[11px] font-bold uppercase tracking-wide text-forest-800 dark:text-cream-100">
              {renderInline(b.text, `h${i}`)}
            </div>
          );
        }
        if (b.type === 'ul') {
          return (
            <ul key={i} className="mt-1.5 space-y-1 list-disc pl-4 marker:text-forest-500">
              {b.items.map((it, j) => <li key={j} className="text-sm leading-relaxed">{renderInline(it, `ul${i}-${j}`)}</li>)}
            </ul>
          );
        }
        if (b.type === 'ol') {
          return (
            <ol key={i} className="mt-1.5 space-y-1 list-decimal pl-4 marker:text-forest-500">
              {b.items.map((it, j) => <li key={j} className="text-sm leading-relaxed">{renderInline(it, `ol${i}-${j}`)}</li>)}
            </ol>
          );
        }
        return <p key={i} className="mt-2 text-sm leading-relaxed first:mt-0">{renderInline(b.text, `p${i}`)}</p>;
      })}
    </div>
  );
}
