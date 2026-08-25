export interface TimelineEntry {
  date: string;
  status: string;
  statusVariant?: 'transit' | 'delivered';
  role: string;
  org: string;
  bullets: string[];
  stack?: string[];
}

export interface TimelineProps {
  items: TimelineEntry[];
}

export function TimelineItem({ date, status, statusVariant = 'delivered', role, org, bullets, stack }: TimelineEntry) {
  const badgeClass = statusVariant === 'transit' ? 'timeline__badge timeline__badge--transit' : 'timeline__badge';
  return (
    <li className="timeline__item">
      <div className="timeline__meta">
        <span className="timeline__date">{date}</span>
        <span className={badgeClass}>{status}</span>
      </div>
      <div className="timeline__node" aria-hidden="true" />
      <div className="timeline__card">
        <h3>
          {role} <span>— {org}</span>
        </h3>
        <ul>
          {bullets.map((bullet) => (
            <li key={bullet}>{bullet}</li>
          ))}
        </ul>
        {stack && stack.length > 0 ? (
          <div className="timeline__stack">
            {stack.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        ) : null}
      </div>
    </li>
  );
}

export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="timeline">
      {items.map((item) => (
        <TimelineItem key={`${item.role}-${item.date}`} {...item} />
      ))}
    </ol>
  );
}
