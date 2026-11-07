import { SITE } from "@config";
import { defineCollection, z } from "astro:content";

const blog = defineCollection({
  type: "content",
  schema: ({ image }) =>
    z.object({
      author: z.string().default(SITE.author),
      pubDatetime: z.date(),
      modDatetime: z.date().optional().nullable(),
      title: z.string(),
      subtitle: z.string().optional(),
      takeaways: z.array(z.string()).optional(),
      // Garden-style metadata
      stage: z.enum(["seedling", "budding", "evergreen"]).default("budding"),
      audience: z.string().optional(), // "Written for" card
      cover: z.string().optional(), // card image, e.g. /figures/f14_round2_circuit.png
      coverAlt: z.string().optional(),
      featured: z.boolean().optional(),
      draft: z.boolean().optional(),
      tags: z.array(z.string()).default([]),
      ogImage: image()
        .refine(img => img.width >= 1200 && img.height >= 630, {
          message: "OpenGraph image must be at least 1200 X 630 pixels!",
        })
        .or(z.string())
        .optional(),
      description: z.string(),
      canonicalURL: z.string().optional(),
    }),
});

export const collections = { blog };
