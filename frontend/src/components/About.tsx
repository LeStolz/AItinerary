import { Box, Flex, ScrollArea } from '@radix-ui/themes';
import ReactMarkdown from 'react-markdown';
import readmeText from '../../README.md?raw';

export function About() {
  return (
    <Flex direction="column" className="h-full w-full">
      <ScrollArea type="always" scrollbars="vertical" className="flex-1">
        <Flex direction="column" align="center" className="w-full">
          <Box className="prose dark:prose-invert max-w-4xl">
            <ReactMarkdown>{readmeText}</ReactMarkdown>
          </Box>
        </Flex>
      </ScrollArea>
    </Flex>
  );
}
