import { useState } from 'react';
import { API_URL } from '../config';
import { Flex, Heading, Text, Card } from '@radix-ui/themes';
import { GoogleLogin } from '@react-oauth/google';

export function Auth() {
  const [error, setError] = useState('');

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      const res = await fetch(`${API_URL}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to authenticate with Google');
      }

      window.location.reload();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <Flex align="center" justify="center" className="h-screen w-screen" style={{ backgroundColor: 'var(--color-page-background)' }}>
      <Card size="4">
        <Flex direction="column" gap="4" align="center">
          <Heading size="7" className="block w-full bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">
            AItinerary
          </Heading>

          <Text size="3" color="gray" align="center">
            Sign in to manage your itineraries.
          </Text>

          <Flex direction="column" align="stretch" className="w-full">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Google Sign-In Failed')}
            />
          </Flex>

          {error && <Text size="2" color="red">{error}</Text>}
        </Flex>
      </Card>
    </Flex>
  );
}
