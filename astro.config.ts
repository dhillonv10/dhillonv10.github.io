import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import react from "@astrojs/react";
import remarkToc from "remark-toc";
import remarkCollapse from "remark-collapse";
import sitemap from "@astrojs/sitemap";
import { SITE } from "./src/config";
import { updatePostDates } from "./scripts/post-dates.mjs";

// record each post's first-commit time (used as its publish date)
updatePostDates();

// Load post images lazily and decode them off the main thread.
function rehypeLazyImages() {
  const walk = (node: any) => {
    if (node.type === "element" && node.tagName === "img") {
      node.properties = {
        ...node.properties,
        loading: "lazy",
        decoding: "async",
      };
    }
    node.children?.forEach(walk);
  };
  return (tree: any) => walk(tree);
}

// https://astro.build/config
export default defineConfig({
  site: SITE.website,
  integrations: [
    tailwind({
      applyBaseStyles: false,
    }),
    react(),
    sitemap(),
  ],
  markdown: {
    rehypePlugins: [rehypeLazyImages],
    remarkPlugins: [
      remarkToc,
      [
        remarkCollapse,
        {
          test: "Table of contents",
        },
      ],
    ],
    shikiConfig: {
      theme: "one-dark-pro",
      wrap: true,
    },
  },
  vite: {
    optimizeDeps: {
      exclude: ["@resvg/resvg-js"],
    },
  },
  scopedStyleStrategy: "where",
});
