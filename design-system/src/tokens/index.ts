export const colors = {
  ink: '#14181B',
  inkSoft: '#1B2023',
  inkLine: '#2B3236',
  paper: '#EDE6D6',
  paperDim: '#9CA3A0',
  kraft: '#D9C8A8',
  kraftLine: '#B8A47D',
  kraftInk: '#2A2116',
  amber: '#E8871E',
  amberSoft: 'rgba(232, 135, 30, .14)',
  steel: '#7FA9C4',
  stampRed: '#C24B3B',
} as const;

export const fonts = {
  display: "'Oswald', 'Arial Narrow', sans-serif",
  body: "'Inter', -apple-system, sans-serif",
  mono: "'IBM Plex Mono', 'SFMono-Regular', monospace",
} as const;

export const layout = {
  max: '1080px',
  edge: 'clamp(20px, 6vw, 64px)',
} as const;
