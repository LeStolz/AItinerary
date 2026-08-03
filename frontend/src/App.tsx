import { useState, useEffect } from 'react'
import { API_URL } from './config'
import { Theme, Flex, Box, Text, Button, Avatar, DropdownMenu, Heading } from '@radix-ui/themes'
import { ThemeToggle } from './components/ThemeToggle'
import { Chat } from './components/Chat'
import { ScrapBook } from './components/ScrapBook'
import { Auth } from './components/Auth'
import { About } from './components/About'
import { MessageSquare, LayoutDashboard, LogOut, Info } from 'lucide-react'

function App() {
  const [isDark, setIsDark] = useState(false)
  const [activeTab, setActiveTab] = useState('planner')
  const [user, setUser] = useState<{ email: string } | null>(null)
  const [loading, setLoading] = useState(true)

  function setTheme(dark: boolean) {
    setIsDark(dark)
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved) {
      setTheme(saved === 'dark')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark)
    }

    fetch(`${API_URL}/api/auth/me`, { credentials: 'include' })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Not logged in');
      })
      .then(data => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, [])

  const handleThemeToggle = (dark: boolean) => {
    setTheme(dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  const handleLogout = async () => {
    await fetch(`${API_URL}/api/auth/logout`, { method: 'POST', credentials: 'include' });
    setUser(null);
  };

  if (loading) {
    return (
      <Theme appearance={isDark ? "dark" : "light"} accentColor="indigo" radius="large">
        <Flex className="h-screen" align="center" justify="center"><Text></Text></Flex>
      </Theme>
    );
  }

  if (!user) {
    return (
      <Theme appearance={isDark ? "dark" : "light"} accentColor="indigo" radius="large">
        <Auth />
      </Theme>
    );
  }

  return (
    <Theme appearance={isDark ? "dark" : "light"} accentColor="indigo" radius="large">
      <Flex direction="row" className="h-screen w-screen">
        <Sidebar
          activeTab={activeTab} setActiveTab={setActiveTab}
          isDark={isDark} handleThemeToggle={handleThemeToggle} user={user} handleLogout={handleLogout}
        />
        <Box className="flex-grow h-screen p-4">
          {activeTab === 'planner' && <Chat />}
          {activeTab === 'scrapbook' && <ScrapBook />}
          {activeTab === 'about' && <About />}
        </Box>
      </Flex>
    </Theme>
  )
}

function Sidebar(
  {
    activeTab, setActiveTab,
    isDark, handleThemeToggle,
    user, handleLogout
  }: {
    activeTab: string; setActiveTab: (tab: string) => void;
    isDark: boolean; handleThemeToggle: (dark: boolean) => void;
    user: { email: string }; handleLogout: () => void
  }
) {
  return (
    <Flex p="4" direction="column" justify="between" className="w-72 shrink-0 bg-[var(--gray-a2)] border-r border-[var(--gray-a4)]">
      <Flex direction="column" className="w-full">
        <Flex align="center" justify="between" mb="4">
          <Heading size="5" weight="bold" className="block w-full bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">
            AItinerary
          </Heading>
          <ThemeToggle isDark={isDark} onToggle={handleThemeToggle} />
        </Flex>

        <Flex direction="column" gap="2" className="w-full">
          {[
            {
              name: 'planner',
              displayName: 'Planner',
              icon: <MessageSquare size={16} />,
            },
            {
              name: 'scrapbook',
              displayName: 'Scrapbook',
              icon: <LayoutDashboard size={16} />,
            },
            {
              name: 'about',
              displayName: 'About',
              icon: <Info size={16} />,
            }
          ].map(tab => (
            <Button
              size="3"
              variant={activeTab === tab.name ? 'soft' : 'ghost'}
              color={activeTab === tab.name ? 'indigo' : 'gray'}
              className="mx-0 justify-start w-full"
              onClick={() => setActiveTab(tab.name)}
            >
              {tab.icon}
              <span>{tab.displayName}</span>
            </Button>
          ))}
        </Flex>
      </Flex>

      <Box pt="4" className="border-t border-[var(--gray-a4)]">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            <Flex direction="column" className="w-full" >
              <Button variant="ghost" size="4" className="justify-start mx-0">
                <Avatar size="3" fallback={user.email.charAt(0).toUpperCase()} radius="full" color="indigo" variant="soft" />
                <Flex direction="column" className="text-left">
                  <Text as="div" size="2" weight="bold" truncate>{user.email.split('@')[0]}</Text>
                  <Text as="div" size="1" color="gray" truncate>{user.email}</Text>
                </Flex>
              </Button>
            </Flex>
          </DropdownMenu.Trigger>
          <DropdownMenu.Content>
            <DropdownMenu.Item color="red" onClick={handleLogout}>
              <LogOut size={14} /> Sign out
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      </Box>
    </Flex>
  )
}

export default App
