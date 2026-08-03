import React, { useState } from 'react';
import { API_URL } from '../config';
import { Flex, Heading, Text, TextField, Button, Card } from '@radix-ui/themes';
import { MailCheck } from 'lucide-react';

export function Auth() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Email is required');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/send-magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to send magic link');
      }

      setSent(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Flex align="center" justify="center" className="h-screen w-screen" style={{ backgroundColor: 'var(--color-page-background)' }}>
      <Card size="4">
        {sent ? (
          <Flex direction="column" gap="4" align="center">
            <MailCheck size={64} color="var(--indigo-9)" />
            <Heading size="6" align="center">Check your email!</Heading>
            <Text size="3" color="gray" align="center">
              We sent a magic link to <strong>{email}</strong>. Click it to sign in.
            </Text>
          </Flex>
        ) : (
          <Flex direction="column" gap="4" align="center">
            <Heading size="7" className="block w-full bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">
              AItinerary
            </Heading>

            <Text size="3" color="gray" align="center">
              Sign in or create an account to manage your itineraries.
            </Text>

            <form onSubmit={handleSubmit} className="w-full">
              <Flex direction="column" gap="4">
                <label>
                  <Text as="div" size="2" mb="1" weight="bold">Email Address</Text>
                  <TextField.Root
                    type="email"
                    size="3"
                    placeholder="traveler@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </label>

                {error && <Text size="2" color="red">{error}</Text>}

                <Button size="3" type="submit" disabled={loading}>
                  {loading ? 'Sending link...' : 'Continue'}
                </Button>
              </Flex>
            </form>
          </Flex>
        )}
      </Card>
    </Flex>
  );
}
