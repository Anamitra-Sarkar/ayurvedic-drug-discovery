/**
 * markdownLite.jsx — small, dependency-free renderer for the plain markdown
 * the real Groq LLM answers come back in (headers, bold/italic, bullet and
 * numbered lists, horizontal rules, pipe tables, inline sup/sub HTML tags
 * for chemistry notation like ICsub50/sub). No npm markdown library was
 * added on purpose (avoids an untested remote-build risk); this covers
 * exactly the patterns real answers have used, not arbitrary markdown.
 */

/** Inline bold/italic markers plus literal sup/sub HTML tags (the LLM
 * emits real <sup>/<sub> for chemistry notation, not markdown for these). */
function renderInline(text, keyPrefix) {
  const parts = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|_(.+?)_|<sup>(.+?)<\/sup>|<sub>(.+?)<\/sub>/g;
  let lastIndex = 0;
  let m;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) parts.push(text.slice(lastIndex, m.index));
    const k = `${keyPrefix}-${key++}`;
    if (m[1] !== undefined) parts.push(<strong key={k}>{m[1]}</strong>);
    else if (m[2] !== undefined || m[3] !== undefined) parts.push(<em key={k}>{m[2] ?? m[3]}</em>);
    else if (m[4] !== undefined) parts.push(<sup key={k}>{m[4]}</sup>);
    else parts.push(<sub key={k}>{m[5]}</sub>);
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

const isTableRow = (line) => /^\|.*\|$/.test(line.trim());
const isSeparatorRow = (line) => /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$/.test(line.trim());
const splitRow = (line) => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());

/** Parse plain markdown lines into block objects (heading/ul/ol/p/hr/table). */
function parseBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let currentList = null;
  const flush = () => { if (currentList) { blocks.push(currentList); currentList = null; } };
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line) { flush(); i += 1; continue; }

    if (isTableRow(line) && i + 1 < lines.length && isSeparatorRow(lines[i + 1])) {
      flush();
      const headers = splitRow(line);
      const rows = [];
      i += 2;
      while (i < lines.length && isTableRow(lines[i])) {
        rows.push(splitRow(lines[i]));
        i += 1;
      }
      blocks.push({ type: 'table', headers, rows });
      continue;
    }
    if (/^-{3,}$/.test(line)) { flush(); blocks.push({ type: 'hr' }); i += 1; continue; }

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
    i += 1;
  }
  flush();
  return blocks;
}

/** Render real (already-boilerplate-stripped) markdown prose as proper
 * headings/lists/tables/paragraphs instead of a wall of text with raw
 * syntax leaking through. */
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
        if (b.type === 'table') {
          return (
            <div key={i} className="mt-2 overflow-x-auto rounded-xl border border-forest-900/10">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="bg-cream-50 dark:bg-white/5">
                    {b.headers.map((h, j) => (
                      <th key={j} className="px-2.5 py-1.5 text-left font-semibold text-forest-800 dark:text-cream-100 border-b border-forest-900/10">{renderInline(h, `th${i}-${j}`)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {b.rows.map((row, ri) => (
                    <tr key={ri} className="border-b last:border-0 border-forest-900/5">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-2.5 py-1.5 align-top text-forest-900/85 dark:text-cream-100/80">{renderInline(cell, `td${i}-${ri}-${ci}`)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <p key={i} className="mt-2 text-sm leading-relaxed first:mt-0">{renderInline(b.text, `p${i}`)}</p>;
      })}
    </div>
  );
}
