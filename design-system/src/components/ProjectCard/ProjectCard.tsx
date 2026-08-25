export interface ProjectBadge {
  label: string;
  href: string;
}

export interface ProjectCta {
  label: string;
  href: string;
}

export interface ProjectCardProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  badge?: ProjectBadge;
  lede: string;
  points: string[];
  stack: string[];
  cta?: ProjectCta;
}

export function ProjectCard({ eyebrow, title, subtitle, badge, lede, points, stack, cta }: ProjectCardProps) {
  return (
    <div className="project-card">
      <div className="project-card__top">
        <div>
          <p className="project-card__eyebrow">{eyebrow}</p>
          <h3>
            {title} <span>{subtitle}</span>
          </h3>
        </div>
        {badge ? (
          <a
            className="project-card__badge"
            href={badge.href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`${title} — visit live site`}
          >
            {/* .dot is defined in shared.css, not ProjectCard.css — shared with Waybill's status indicator */}
            <i className="dot" aria-hidden="true" />
            {badge.label}
          </a>
        ) : null}
      </div>

      <p className="project-card__lede">{lede}</p>

      <ul className="project-card__points">
        {points.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>

      <div className="project-card__stack">
        {stack.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>

      {cta ? (
        <div className="hero__actions">
          <a className="btn btn--stamp" href={cta.href} target="_blank" rel="noopener noreferrer">
            {cta.label} →
          </a>
        </div>
      ) : null}
    </div>
  );
}
