import { Octagon, Triangle, Diamond, Circle, CircleDashed } from 'lucide-react';

const LEVEL_CONFIG = {
  U1: { label: 'Immediate', icon: Octagon },
  U2: { label: 'Urgent', icon: Triangle },
  U3: { label: 'Soon', icon: Diamond },
  U4: { label: 'Standard', icon: Circle },
  U5: { label: 'Low', icon: CircleDashed },
};

export default function UrgencyChip({ level }) {
  if (!level) return null;
  const config = LEVEL_CONFIG[level];
  const Icon = config ? config.icon : Circle;
  const label = config ? config.label : 'Unknown';

  return (
    <span className={`urgency-chip urgency-${level.toLowerCase()}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
      <Icon size={14} strokeWidth={3} />
      <span>{level} {label}</span>
    </span>
  );
}
