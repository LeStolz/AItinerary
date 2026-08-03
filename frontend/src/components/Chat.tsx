import React, { useState, useRef, useEffect } from 'react';
import { API_URL } from '../config';
import { Box, Card, Flex, Text, TextField, Button, ScrollArea, Heading, Badge, Skeleton } from '@radix-ui/themes';
import { Send, Map, Search, Clock, CheckCircle2, LayoutList } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  sender: string;
  content: string;
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [activeAgent, setActiveAgent] = useState('Orchestrator Agent');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/chat/history`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setMessages(data.map(msg => ({
            id: Date.now().toString() + Math.random(),
            sender: msg.sender,
            content: msg.content,
            type: msg.type
          })));
          setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'auto' }), 100);
        }
      })
      .catch(err => console.error("Failed to load chat history:", err))
      .finally(() => setIsInitialLoad(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'User',
      content: input,
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setActiveAgent('Orchestrator Agent');

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content }),
        credentials: 'include'
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let currentEventStr = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        currentEventStr += chunk;

        // Process SSE lines
        const lines = currentEventStr.split('\n');
        currentEventStr = lines.pop() || ''; // Keep the last incomplete line

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.active_agent) {
                setActiveAgent(data.active_agent);
              }

              if (data.sender && data.content) {
                setMessages(prev => [...prev, {
                  id: Date.now().toString() + Math.random(),
                  sender: data.sender,
                  content: data.content,
                  type: data.sender === 'System' ? 'system' : 'agent'
                }]);
              }
            } catch (err) {
              console.error("Parse error on chunk:", dataStr);
            }
          }
        }
      }
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'System',
        content: `Error: ${error.message}`,
        type: 'system'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentIcon = (sender: string) => {
    switch (sender) {
      case 'Scrapbook Agent': return <Search size={16} />;
      case 'Logistics Agent': return <Clock size={16} />;
      case 'Booking Agent': return <Map size={16} />;
      case 'System': return <CheckCircle2 size={16} />;
      case 'Orchestrator Agent': return <LayoutList size={16} />;
      default: return <LayoutList size={16} />;
    }
  };

  const getAgentColor = (sender: string) => {
    switch (sender) {
      case 'Scrapbook Agent': return 'blue';
      case 'Logistics Agent': return 'amber';
      case 'Booking Agent': return 'green';
      case 'System': return 'red';
      case 'Orchestrator Agent': return 'purple';
      default: return 'gray';
    }
  };

  return (
    <Flex direction="column" className="h-full w-full">

      {/* Messages Area */}
      <ScrollArea type="always" scrollbars="vertical" className="flex-1">
        <Flex direction="column" align="center">
          <Flex direction="column" gap="4" className="w-full max-w-3xl">

            {isInitialLoad ? (
              <Flex direction="column" gap="4" className="w-full mt-8">
                <Flex justify="end" className="w-full">
                  <Skeleton width="40%" height="4rem" />
                </Flex>
                {[1, 3].map(i => (
                  <Flex justify="start" className="w-full">
                    <Box width="100%">
                      <Flex align="center" gap="2" mb="1">
                        <Skeleton width="8rem" height="2rem" />
                      </Flex>
                      <Skeleton width="100%" height={`${i * 4}rem`} />
                    </Box>
                  </Flex>
                ))}
              </Flex>
            ) : messages.length === 0 && (
              <Flex align="center" justify="center" className="min-h-96">
                <Heading size="7" className="p-16 bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">
                  Where to next?
                </Heading>
              </Flex>
            )}

            {messages.map((msg) => (
              <Flex key={msg.id} justify={msg.sender === 'User' ? 'end' : 'start'} width="100%">
                <Box maxWidth="85%">
                  {msg.sender !== 'User' && (
                    <Flex align="center" gap="2" mb="1">
                      <Badge color={getAgentColor(msg.sender) as any} variant="soft" radius="full">
                        {getAgentIcon(msg.sender)}
                        <Text>{msg.sender}</Text>
                      </Badge>
                    </Flex>
                  )}
                  <Card
                    size="2"
                    variant={msg.sender === 'User' ? 'surface' : 'ghost'}
                    className={`${msg.sender === 'User' ? 'border border-[var(--accent-a3)]' : ''}`}
                  >
                    <Box className="prose dark:prose-invert">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </Box>
                  </Card>
                </Box>
              </Flex>
            ))}

            {isLoading && (
              <Flex justify="start">
                <Badge color={getAgentColor(activeAgent)} variant="soft" radius="full">
                  <Text>{`${activeAgent} is working...`}</Text>
                </Badge>
              </Flex>
            )}

            <div ref={bottomRef} className="h-4" />
          </Flex>
        </Flex>
      </ScrollArea>

      <Box p="4">
        <Flex justify="center">
          <Box className="w-full max-w-3xl">
            <form onSubmit={handleSubmit}>
              <Flex gap="4">
                <TextField.Root
                  placeholder="Plan a 4-day trip to Paris for under $150/night."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isLoading}
                  size="3"
                  radius="full"
                  className="flex-1"
                />
                <Button type="submit" size="3" radius="full" disabled={isLoading || !input.trim()}>
                  <Send size={18} />
                </Button>
              </Flex>
            </form>
            <Flex justify="center" mt="2">
              <Text size="1" color="gray">AItinerary agents can make mistakes. Please verify important bookings.</Text>
            </Flex>
          </Box>
        </Flex>
      </Box>

    </Flex>
  );
}
