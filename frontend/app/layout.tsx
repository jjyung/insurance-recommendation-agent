import type { Metadata } from 'next';
import { IBM_Plex_Mono, Space_Grotesk } from 'next/font/google';
import type { ReactNode } from 'react';

import './globals.css';

const sans = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
});

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'ADK Web Mock UI',
  description:
    'A Next.js mock frontend inspired by the ADK Web development interface.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang='zh-Hant'>
      <body className={`${sans.variable} ${mono.variable}`}>{children}</body>
    </html>
  );
}
