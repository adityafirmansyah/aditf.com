import { ProjectCard } from '@aditf/design-system';

const wrapperStyle = { background: 'var(--ink)', padding: 24, maxWidth: 720 };

export function WithLiveBadge() {
  return (
    <div style={wrapperStyle}>
      <ProjectCard
        eyebrow="Solo Build — Full-Stack Rust"
        title="GainForge"
        subtitle="Gamified Fitness RPG"
        badge={{ label: 'LIVE', href: 'https://gainforgeapp.com' }}
        lede="GainForge turns real workouts into RPG quests — users earn XP, level up a character, and grow four stats by completing daily training sessions."
        points={[
          'Full Rust stack front-to-back — Leptos (WASM) frontend and an Axum backend share a single DTO crate.',
          'Designed the quest/XP/leveling system and a 4-stat character model.',
        ]}
        stack={['Rust', 'Leptos (WASM)', 'Axum', 'PostgreSQL', 'Docker']}
        cta={{ label: 'Visit GainForge', href: 'https://gainforgeapp.com' }}
      />
    </div>
  );
}

export function WithoutBadgeOrCta() {
  return (
    <div style={wrapperStyle}>
      <ProjectCard
        eyebrow="Solo Build — Full-Stack JavaScript"
        title="Cover Letter Generator"
        subtitle="AI Cover Letter Tool"
        lede="Users build a profile, type in a job title and description, and get a tailored, editable cover letter back."
        points={[
          'Prompt builder calls an LLM API to draft the letter, followed by a humanization pass.',
          'Full auth/profile/letter-history schema in PostgreSQL behind JWT auth.',
        ]}
        stack={['React', 'Vite', 'Tailwind', 'Node.js', 'Express', 'PostgreSQL']}
      />
    </div>
  );
}
