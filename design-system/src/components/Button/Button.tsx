import type { AnchorHTMLAttributes, ReactNode } from 'react';

export type ButtonVariant = 'stamp' | 'ghost';

export interface ButtonProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  variant: ButtonVariant;
  children: ReactNode;
}

export function Button({ variant, children, className, ...rest }: ButtonProps) {
  const variantClass = variant === 'stamp' ? 'btn--stamp' : 'btn--ghost';
  const classes = ['btn', variantClass, className].filter(Boolean).join(' ');
  return (
    <a className={classes} {...rest}>
      {children}
    </a>
  );
}
