import React from 'react';
import clsx from 'clsx';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverEffect?: boolean;
  className?: string;
  glow?: 'cyan' | 'amber' | 'red' | 'none';
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  hoverEffect = false,
  className,
  glow = 'none',
  ...props
}) => {
  return (
    <div
      className={clsx(
        'glass-card rounded-2xl p-6 relative overflow-hidden',
        hoverEffect && 'glass-card-hover cursor-pointer',
        glow === 'cyan' && 'glow-cyan border-primary/40',
        glow === 'amber' && 'glow-amber border-status-warning/40',
        glow === 'red' && 'glow-red border-status-error/40',
        className
      )}
      {...props}
    >
      {/* Specular highlight border on top */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
      {children}
    </div>
  );
};
