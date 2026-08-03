import React, { useState, useEffect, useRef } from 'react';
import { API_URL } from '../config';
import { Box, Card, Flex, Text, Heading, Button, Dialog, ScrollArea, IconButton, DropdownMenu, TextArea, Tabs } from '@radix-ui/themes';
import { Plus, Trash, Edit2, FileText, MapPin, User, Upload } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface TravelCard {
  id: number;
  type: string;
  title: string;
  content: string;
}

export function ScrapBook() {
  const [cards, setCards] = useState<TravelCard[]>([
    {
      id: -1,
      type: 'preference',
      title: '',
      content: ''
    }
  ]);
  const [openDialog, setOpenDialog] = useState<string | null>(null);
  const [editingCardId, setEditingCardId] = useState<number | null>(null);
  const [markdown, setMarkdown] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadCards = async () => {
    try {
      const res = await fetch(`${API_URL}/api/cards`, { credentials: 'include' });
      const data = await res.json();
      setCards(data);
    } catch (e) {
      console.error("Failed to load cards", e);
    }
  };

  useEffect(() => {
    loadCards();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`${API_URL}/api/cards/${id}`, { method: 'DELETE', credentials: 'include' });
    loadCards();
  };

  const extractTitle = (md: string) => {
    const match = md.match(/^#\s+(.+)$/m);
    return match ? match[1] : 'Untitled';
  };

  const handleSave = async (type: string) => {
    const payload = {
      type,
      title: extractTitle(markdown),
      content: JSON.stringify({ markdown })
    };

    if (editingCardId) {
      await fetch(`${API_URL}/api/cards/${editingCardId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include'
      });
    } else {
      await fetch(`${API_URL}/api/cards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include'
      });
    }

    setOpenDialog(null);
    setEditingCardId(null);
    setMarkdown('');
    loadCards();
  };

  const handleEdit = (card: TravelCard) => {
    let data;
    try {
      data = JSON.parse(card.content);
    } catch {
      data = { markdown: card.content };
    }
    const mdContent = data.markdown || card.content;

    setMarkdown(mdContent);
    setEditingCardId(card.id);
    setOpenDialog(card.type);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setMarkdown(`# ${file.name.replace(/\.[^/.]+$/, "")}\n\n${text}`);
      setOpenDialog('note');
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const renderCardContent = (card: TravelCard) => {
    let data;
    try {
      data = JSON.parse(card.content);
    } catch {
      data = { markdown: card.content };
    }

    const mdContent = data.markdown || card.content;

    return mdContent;
  };

  const getCardIcon = (type: string) => {
    switch (type) {
      case 'preference': return <User size={16} />;
      case 'destination': return <MapPin size={16} />;
      case 'note': return <FileText size={16} />;
      default: return <FileText size={16} />;
    }
  };

  return (
    <Flex direction="column" className="h-full w-full">
      <Flex justify="between" align="center" pb="3" className="border-b border-[var(--gray-a4)]">
        <Box className="flex-1">
          <Heading size="5" weight="bold">Scrapbook</Heading>
          <Text color="gray" size="2">Your travel board for preferences, destinations, and journals.</Text>
        </Box>
        <Flex gap="3">
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".txt,.md" className="hidden" />
          <Button variant="soft" onClick={() => fileInputRef.current?.click()}>
            <Upload size={16} /> Upload Text
          </Button>

          <DropdownMenu.Root>
            <DropdownMenu.Trigger>
              <Button size="2"><Plus size={16} /> Add Card</Button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Content>
              <DropdownMenu.Item onClick={() => { setEditingCardId(null); setMarkdown('# New Preference\n\n'); setOpenDialog('preference') }}>
                <User size={14} /> Preference
              </DropdownMenu.Item>
              <DropdownMenu.Item onClick={() => { setEditingCardId(null); setMarkdown('# New Destination\n\n'); setOpenDialog('destination') }}>
                <MapPin size={14} /> Destination
              </DropdownMenu.Item>
              <DropdownMenu.Item onClick={() => { setEditingCardId(null); setMarkdown('# New Journal Entry\n\n'); setOpenDialog('note') }}>
                <FileText size={14} /> Journal
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Root>
        </Flex>
      </Flex>

      <ScrollArea type="always" scrollbars="vertical" className="flex-1 mt-4">
        <div className="flex flex-wrap items-start gap-4 pr-4">
          {cards.map(card => (
            <Card
              key={card.id} size="2"
              className="w-fit max-w-full relative group shadow-sm hover:shadow-md dark:shadow-black/40 transition-shadow"
            >
              <Flex justify="between" align="center" mb="2">
                <Flex align="center" gap="2">
                  {getCardIcon(card.type)}
                  <Text weight="bold" size="3" truncate className="max-w-3xl">{card.title}</Text>
                </Flex>
                <Flex gap="2" className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <IconButton size="1" variant="ghost" color="gray" onClick={() => handleEdit(card)}>
                    <Edit2 size={16} />
                  </IconButton>
                  <IconButton size="1" variant="ghost" color="red" onClick={() => handleDelete(card.id)}>
                    <Trash size={16} />
                  </IconButton>
                </Flex>
              </Flex>
              <ScrollArea type="auto" scrollbars="vertical">
                <Box className="prose dark:prose-invert text-sm max-h-64">
                  <ReactMarkdown>{renderCardContent(card)}</ReactMarkdown>
                </Box>
              </ScrollArea>
            </Card>
          ))}
          {cards.length === 0 && (
            <Heading size="7" className="block w-full bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">
              Add a card to get started!
            </Heading>
          )}
        </div>
      </ScrollArea>

      <Dialog.Root open={openDialog !== null} onOpenChange={(open) => {
        if (!open) {
          setOpenDialog(null);
          setEditingCardId(null);
        }
      }}>
        <Dialog.Content className="max-w-2xl w-full">
          <Dialog.Title>{editingCardId ? 'Edit' : 'Add'} {openDialog}</Dialog.Title>
          <Dialog.Description size="2" color="gray" mb="4">
            Use Markdown to format your card. The first (# Title) will be used as the card title.
          </Dialog.Description>

          <Tabs.Root defaultValue="edit">
            <Tabs.List>
              <Tabs.Trigger value="edit">Edit Markdown</Tabs.Trigger>
              <Tabs.Trigger value="preview">Preview Markdown</Tabs.Trigger>
            </Tabs.List>

            <Box pt="3">
              <Tabs.Content value="edit">
                <TextArea
                  value={markdown}
                  onChange={e => setMarkdown(e.target.value)}
                  placeholder="# My Title&#10;&#10;Write your markdown here."
                  rows={15}
                  className="font-mono"
                />
              </Tabs.Content>

              <Tabs.Content value="preview">
                <ScrollArea type="always" scrollbars="vertical" className="h-[20rem] border border-[var(--gray-a4)] p-4 rounded-md">
                  <Box className="prose dark:prose-invert max-w-none text-sm">
                    <ReactMarkdown>{markdown}</ReactMarkdown>
                  </Box>
                </ScrollArea>
              </Tabs.Content>
            </Box>
          </Tabs.Root>

          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">Cancel</Button>
            </Dialog.Close>
            <Button onClick={() => handleSave(openDialog!)}>Save Card</Button>
          </Flex>
        </Dialog.Content>
      </Dialog.Root>
    </Flex>
  );
}
