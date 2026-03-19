# Frontend Architecture

The frontend is built with **Next.js 14** using the App Router, heavily utilizing client-side React features for real-time interactions.

## Design System

- **Styling**: Tailwind CSS is used for all styling.
- **Theme**: Dark mode default, leveraging a "glassmorphism" aesthetic with deep blur effects, subtle gradients to communicate trust and modernity, keeping in line with typical modern FinTech UIs.
- **Icons**: `lucide-react` for crisp SVG icons.

## Key Components

### `app/page.tsx`
The primary Chat interface. It maintains the message history state and stream status.

### Streaming Process
- The frontend sends a POST request with the user's input to the FastAPI backend.
- It processes Server-Sent Events (SSE) manually using the native Web `ReadableStream` API.
- Each chunk is incrementally appended to the `currentStreamingMessage` state, which causes React to re-render the terminal-like UI.
- JSON payloads sent from the backend are safely parsed. If a payload contains `sources` arrays or `response_type: refusal`, the frontend applies specific UI badges and renders citation source cards.

### Source Deduplication
The frontend includes explicit logic to map through the `msg.sources` array, running a `.filter()` matching `source_url` and `fund_name` to ensure citation cards do not duplicate visibly to the user.
