// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Protostar",
  tagline: "StarkNet smart contract development toolchain",
  url: "https://docs.swmansion.com",
  baseUrl: "/protostar/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  organizationName: "software-mansion",
  projectName: "protostar",
  trailingSlash: false,
  deploymentBranch: "gh-pages",

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          // Please change this to your repo.
          editUrl: ({ docPath }) =>
            `https://github.com/software-mansion/protostar/tree/master/website/docs/${docPath}`,
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  headTags: [
    {
      tagName: "link",
      attributes: {
        rel: "manifest",
        content: "/protostar/manifest.json",
      }
    },
    {
      tagName: "link",
      attributes: {
        rel: "icon",
        href: "/protostar/favicon.ico",
        sizes: "any"
      }
    },
    {
      tagName: "link",
      attributes: {
        rel: "icon",
        href: "/protostar/favicon.svg",
        type: "image/svg+xml"
      }
    },
    {
      tagName: "link",
      attributes: {
        rel: "apple-touch-icon",
        content: "/protostar/apple-touch-icon.png"
      }
    },
    {
      tagName: "meta",
      attributes: {
        name: "apple-mobile-web-app-title",
        content: "Protostar"
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:type",
        content: "website"
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:image",
        content: "https://docs.swmansion.com/protostar/og-image.png"
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:image:alt",
        content: "StarkNet smart contract development toolchain."
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:image:type",
        content: "image/png"
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:image:width",
        content: "1280"
      }
    },
    {
      tagName: "meta",
      attributes: {
        property: "og:image:height",
        content: "640"
      }
    },
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        logo: {
          alt: "Protostar",
          src: "img/protostar-wide--light.svg",
          srcDark: "img/protostar-wide--dark.svg",
        },
        items: [
          {
            type: "docSidebar",
            position: "left",
            sidebarId: "tutorials",
            label: "Tutorials",
          },
          {
            type: "doc",
            position: "left",
            docId: "cli-reference",
            label: "CLI Reference",
          },
          {
            href: "https://github.com/software-mansion/protostar",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              {
                label: "Tutorials",
                to: "/docs/tutorials/introduction",
              },
            ],
          },
          {
            title: "Community",
            items: [
              {
                label: "Discord",
                href: "https://discord.com/invite/QypNMzkHbc",
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Software Mansion. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ["toml"],
      },
      algolia: {
        /*
         * `appId` and `apiKey` are not secrets and can be added to your Git repository
         * https://docusaurus.io/blog/2021/11/21/algolia-docsearch-migration#upgrading-your-docusaurus-site
         */
        appId: 'QNXZL3QPUX',
        apiKey: '24238025ee666b83f52e6b00ff6f78d2',
        indexName: 'protostar',
        contextualSearch: true,
      },
    }),

  plugins: [
    ['@docusaurus/plugin-client-redirects', {
      redirects: [
        // NOTE: Old links before 2022-07-21
        //   To test, check if links in this blog post work:
        //   https://mirror.xyz/onlydust.eth/uhKk_3p34mE0oFUxkIYlCsjkE7ZvUfSFWU83UM9_w-w
        {
          to: '/docs/tutorials/compiling',
          from: '/docs/tutorials/guides/compiling',
        },
        {
          to: '/docs/tutorials/dependencies-management',
          from: '/docs/tutorials/guides/dependencies-management',
        },
        {
          to: '/docs/tutorials/interacting-with-starknet/deploy/',
          from: '/docs/tutorials/guides/deploying',
        },
        {
          to: '/docs/tutorials/testing',
          from: '/docs/tutorials/guides/testing',
        },
        {
          to: '/docs/tutorials/migrations',
          from: '/docs/tutorials/deploying/migrations',
        },
        {
          to: '/docs/tutorials/interacting-with-starknet',
          from: '/docs/tutorials/deploying/cli'
        },
        {
          to: '/docs/tutorials/migrations/',
          from: [
              '/docs/tutorials/migrations/call',
              '/docs/tutorials/migrations/declare',
              '/docs/tutorials/migrations/deploy-contract',
              '/docs/tutorials/migrations/invoke',
              '/docs/tutorials/migrations/network-config'
          ]
        }
      ]
    }],
  ],
};

module.exports = config;
