import type { CollectionEntry } from "astro:content";

export type PostKind = "feature" | "note";

/** A post's kind: its `type` if set, else `featured: true` means feature, else note. */
const postKind = ({ data }: CollectionEntry<"blog">): PostKind =>
  data.type ?? (data.featured ? "feature" : "note");

export default postKind;
