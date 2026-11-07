// Placeholder shelf. Replace with your own books.
// Add `cover: "/books/my-book.jpg"` (file in public/books/) to show a real cover;
// otherwise a typographic cover is drawn from `color`.
export type Book = {
  title: string;
  author: string;
  color: string; // cover background
  ink?: string; // cover text colour (default: white)
  cover?: string;
  url?: string;
};

export const BOOKS: Book[] = [
  {
    title: "Normal Accidents",
    author: "Charles Perrow",
    color: "#7a2e2a",
  },
  {
    title: "The Checklist Manifesto",
    author: "Atul Gawande",
    color: "#e9e2cf",
    ink: "#2b2a27",
  },
  {
    title: "The Emperor of All Maladies",
    author: "Siddhartha Mukherjee",
    color: "#1f4b57",
  },
  {
    title: "Thinking in Systems",
    author: "Donella Meadows",
    color: "#4d6b3c",
  },
  {
    title: "The Structure of Scientific Revolutions",
    author: "Thomas S. Kuhn",
    color: "#d9a441",
    ink: "#2b2a27",
  },
  {
    title: "Gödel, Escher, Bach",
    author: "Douglas Hofstadter",
    color: "#2d2a4a",
  },
  {
    title: "The Design of Everyday Things",
    author: "Don Norman",
    color: "#c4552d",
  },
  {
    title: "The Soul of a New Machine",
    author: "Tracy Kidder",
    color: "#3b5c8a",
  },
];
