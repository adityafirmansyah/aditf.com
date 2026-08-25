import { useState } from 'react';

export interface NavLink {
  label: string;
  href: string;
  index: string;
}

export interface NavProps {
  mark: string;
  links: NavLink[];
}

export function Nav({ mark, links }: NavProps) {
  const [open, setOpen] = useState(false);

  return (
    <header className="nav">
      <a href="#top" className="nav__mark" aria-label="Back to top">
        {mark}
      </a>
      <button
        className="nav__toggle"
        aria-expanded={open}
        aria-controls="navLinks"
        aria-label="Toggle navigation"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span></span><span></span><span></span>
      </button>
      <nav id="navLinks" className={`nav__links${open ? ' is-open' : ''}`}>
        {links.map((link) => (
          <a key={link.href} href={link.href} onClick={() => setOpen(false)} aria-label={`${link.index}${link.label}`}>
            <span className="idx">{link.index}</span>
            {link.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
