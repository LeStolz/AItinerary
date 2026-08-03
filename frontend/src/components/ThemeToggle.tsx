import { IconButton } from '@radix-ui/themes';
import { Sun, Moon } from 'lucide-react';

interface ThemeToggleProps {
  onToggle: (isDark: boolean) => void;
  isDark: boolean;
}

export function ThemeToggle({ onToggle, isDark }: ThemeToggleProps) {
  return (
    <IconButton
      size="2"
      variant="soft"
      color="gray"
      radius="full"
      onClick={() => onToggle(!isDark)}
      aria-label="Toggle Theme"
    >
      {isDark ? <Moon size={16} /> : <Sun size={16} />}
    </IconButton>
  );
}
