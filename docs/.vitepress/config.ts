import { defineConfig } from 'vitepress'

const base = '/ai-coding-kit/'

export default defineConfig({
  base,
  title: 'ai-coding-kit',
  description: 'One kit for all AI coding tools — Agent Skills, MCP sync, iOS engineering rules, and RAG gateway',
  lang: 'en-US',
  lastUpdated: true,
  cleanUrls: true,
  ignoreDeadLinks: false,

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/ai-coding-kit/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#0A84FF' }],
  ],

  themeConfig: {
    logo: false,
    siteTitle: 'ai-coding-kit',

    nav: [
      { text: 'Home', link: '/' },
      { text: 'iOS Engineer', link: '/ios-engineer/' },
      { text: 'GitHub', link: 'https://github.com/i-stack/ai-coding-kit' },
    ],

    sidebar: {
      '/ios-engineer/': [
        {
          text: 'iOS Engineer',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/ios-engineer/' },
            { text: 'Rule Index', link: '/ios-engineer/rule-index' },
            { text: 'References', link: '/ios-engineer/references' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/i-stack/ai-coding-kit' },
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2025–2026 i-stack',
    },

    search: {
      provider: 'local',
    },

    editLink: {
      pattern: 'https://github.com/i-stack/ai-coding-kit/edit/feature_3.0.0/docs/:path',
    },
  },
})
