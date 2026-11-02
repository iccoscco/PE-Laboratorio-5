import { openDatabase } from "./database.js";
import { createApp } from "./app.js";
const db = openDatabase(
  process.env.DATABASE_PATH || "./data/raiz.db",
  process.env.SEED_DEMO !== "false",
);
const port = Number(process.env.PORT || 4000);
const server = createApp(db).listen(port, "0.0.0.0", () =>
  console.log(`Raíz API disponible en http://localhost:${port}/api/health`),
);
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () =>
    server.close(() => {
      db.close();
      process.exit(0);
    }),
  );
