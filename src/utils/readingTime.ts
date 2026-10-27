/** Estimated minutes to read a markdown body (~225 wpm, minimum 1). */
const readingTime = (body: string) =>
  Math.max(1, Math.round(body.split(/\s+/).filter(Boolean).length / 225));

export default readingTime;
