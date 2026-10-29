# frontend

## Quick start
from this folder
```bash
npm install
npm run dev
```

## Commands
```bash
npm run dev # for development
npm run build # for production
```

## Where and what to change

- **New page:** Create a component in `src/views` and register it in `src/router`
- **Repeating interface elements** in `src/components`
- **Use** `src/api/client.js` **for requests.**
- **Styling:** global rules go in `styles/main.css`, followed by `styles/auth.css` and similar files containing styles for specific components.
- **If you change the backend address** (to something other than `localhost:8000`), you need to update the default address in `vite.config.js` under `server.proxy['/v1'].target`.

## Principles

Keep the structure simple: `views` handle pages, `components` manage reusable parts, `stores` deal with state, `api` covers the network layer, and `styles` handle the look and feel. Only add a new abstraction when it’s truly necessary.

