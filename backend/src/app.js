import express from "express";
import cors from "cors";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import { z } from "zod";
import { randomBytes, createHash } from "node:crypto";
import { hashPassword, verifyPassword, transaction } from "./database.js";

const text = z.string().trim().min(1).max(120);
const productSchema = z.object({
  name: text,
  category: text,
  priceCents: z.number().int().min(1).max(100000000),
  stock: z.number().int().min(0).max(100000),
  minStock: z.number().int().min(0).max(100000),
});
const customerSchema = z.object({
  name: text,
  phone: z.string().trim().max(25).default(""),
  email: z.union([z.email(), z.literal("")]).default(""),
});
const digest = (token) => createHash("sha256").update(token).digest("hex");
const day = (date) =>
  new Date(date).toLocaleDateString("en-CA", { timeZone: "America/Lima" });
function fail(status, message) {
  const err = new Error(message);
  err.status = status;
  throw err;
}
const publicUser = (u) => ({
  id: u.id,
  name: u.name,
  email: u.email,
  business: u.business,
  phone: u.phone,
  location: u.location,
});
export function createApp(db) {
  const app = express();
  app.disable("x-powered-by");
  app.use(helmet());
  app.use(
    cors({
      origin: (process.env.CORS_ORIGIN || "http://localhost:8081").split(","),
    }),
  );
  app.use(express.json({ limit: "64kb" }));
  app.get("/api/health", (_, res) =>
    res.json({
      status: "ok",
      service: "raiz-api",
      paymentsMode: "manual-demo",
    }),
  );
  const authLimit = rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: 30,
    standardHeaders: "draft-8",
    legacyHeaders: false,
    message: { error: "Demasiados intentos. Intenta en 15 minutos." },
  });
  function session(user, res, status = 200) {
    const token = randomBytes(32).toString("hex");
    const expiresAt = Date.now() + 7 * 86400000;
    db.prepare("INSERT INTO sessions VALUES(?,?,?)").run(
      digest(token),
      user.id,
      expiresAt,
    );
    res.status(status).json({ token, expiresAt, user: publicUser(user) });
  }
  app.post("/api/auth/login", authLimit, (req, res) => {
    const data = z
      .object({ email: z.email(), password: z.string().min(1).max(128) })
      .parse(req.body);
    const user = db
      .prepare("SELECT * FROM users WHERE email=?")
      .get(data.email.toLowerCase());
    if (!user || !verifyPassword(data.password, user.password))
      fail(401, "Correo o contraseña incorrectos.");
    session(user, res);
  });
  app.post("/api/auth/register", authLimit, (req, res) => {
    const data = z
      .object({
        name: text,
        business: text,
        email: z.email(),
        password: z.string().min(8).max(128),
      })
      .parse(req.body);
    if (
      db
        .prepare("SELECT id FROM users WHERE email=?")
        .get(data.email.toLowerCase())
    )
      fail(409, "Este correo ya está registrado.");
    const id = Number(
      db
        .prepare(
          "INSERT INTO users(name,business,email,password) VALUES(?,?,?,?)",
        )
        .run(
          data.name,
          data.business,
          data.email.toLowerCase(),
          hashPassword(data.password),
        ).lastInsertRowid,
    );
    session(db.prepare("SELECT * FROM users WHERE id=?").get(id), res, 201);
  });
  app.use("/api", (req, res, next) => {
    const token = req.headers.authorization?.replace(/^Bearer /, "");
    if (!token)
      return res.status(401).json({ error: "Inicia sesión para continuar." });
    const row = db
      .prepare(
        "SELECT user_id FROM sessions WHERE token_hash=? AND expires_at>?",
      )
      .get(digest(token), Date.now());
    if (!row)
      return res
        .status(401)
        .json({ error: "Tu sesión expiró. Vuelve a iniciar sesión." });
    req.userId = row.user_id;
    req.token = token;
    next();
  });
  app.get("/api/me", (req, res) =>
    res.json(
      publicUser(db.prepare("SELECT * FROM users WHERE id=?").get(req.userId)),
    ),
  );
  app.patch("/api/me", (req, res) => {
    const d = z
      .object({
        name: text,
        business: text,
        phone: z.string().trim().max(25),
        location: text,
      })
      .parse(req.body);
    db.prepare(
      "UPDATE users SET name=?,business=?,phone=?,location=? WHERE id=?",
    ).run(d.name, d.business, d.phone, d.location, req.userId);
    res.json(
      publicUser(db.prepare("SELECT * FROM users WHERE id=?").get(req.userId)),
    );
  });
  app.post("/api/auth/logout", (req, res) => {
    db.prepare("DELETE FROM sessions WHERE token_hash=?").run(
      digest(req.token),
    );
    res.status(204).end();
  });
  app.get("/api/products", (req, res) =>
    res.json(
      db
        .prepare(
          "SELECT id,name,category,price_cents AS priceCents,stock,min_stock AS minStock FROM products WHERE user_id=? AND active=1 ORDER BY id DESC",
        )
        .all(req.userId),
    ),
  );
  app.post("/api/products", (req, res) => {
    const d = productSchema.parse(req.body);
    const r = db
      .prepare(
        "INSERT INTO products(user_id,name,category,price_cents,stock,min_stock) VALUES(?,?,?,?,?,?)",
      )
      .run(req.userId, d.name, d.category, d.priceCents, d.stock, d.minStock);
    res.status(201).json({ id: Number(r.lastInsertRowid), ...d });
  });
  app.put("/api/products/:id", (req, res) => {
    const d = productSchema.parse(req.body);
    const r = db
      .prepare(
        "UPDATE products SET name=?,category=?,price_cents=?,stock=?,min_stock=? WHERE id=? AND user_id=? AND active=1",
      )
      .run(
        d.name,
        d.category,
        d.priceCents,
        d.stock,
        d.minStock,
        req.params.id,
        req.userId,
      );
    if (!r.changes) fail(404, "Producto no encontrado.");
    res.json({ id: Number(req.params.id), ...d });
  });
  app.delete("/api/products/:id", (req, res) => {
    const r = db
      .prepare(
        "UPDATE products SET active=0 WHERE id=? AND user_id=? AND active=1",
      )
      .run(req.params.id, req.userId);
    if (!r.changes) fail(404, "Producto no encontrado.");
    res.status(204).end();
  });
  app.get("/api/customers", (req, res) =>
    res.json(
      db
        .prepare(
          "SELECT id,name,phone,email FROM customers WHERE user_id=? ORDER BY name",
        )
        .all(req.userId),
    ),
  );
  app.post("/api/customers", (req, res) => {
    const d = customerSchema.parse(req.body);
    const r = db
      .prepare(
        "INSERT INTO customers(user_id,name,phone,email) VALUES(?,?,?,?)",
      )
      .run(req.userId, d.name, d.phone, d.email);
    res.status(201).json({ id: Number(r.lastInsertRowid), ...d });
  });
  app.put("/api/customers/:id", (req, res) => {
    const d = customerSchema.parse(req.body);
    const r = db
      .prepare(
        "UPDATE customers SET name=?,phone=?,email=? WHERE id=? AND user_id=?",
      )
      .run(d.name, d.phone, d.email, req.params.id, req.userId);
    if (!r.changes) fail(404, "Cliente no encontrado.");
    res.json({ id: Number(req.params.id), ...d });
  });
  function salesFor(userId) {
    return db
      .prepare(
        `SELECT s.id,s.customer_name AS customerName,s.total_cents AS totalCents,s.status,s.created_at AS createdAt,p.method,p.reference,p.created_at AS paidAt FROM sales s LEFT JOIN payments p ON p.sale_id=s.id WHERE s.user_id=? ORDER BY s.created_at DESC,s.id DESC`,
      )
      .all(userId)
      .map((s) => ({
        ...s,
        items: db
          .prepare(
            "SELECT product_id AS productId,name,quantity,price_cents AS priceCents FROM sale_items WHERE sale_id=?",
          )
          .all(s.id),
      }));
  }
  app.get("/api/sales", (req, res) => res.json(salesFor(req.userId)));
  app.post("/api/sales", (req, res) => {
    const d = z
      .object({
        customerId: z.number().int().positive().nullable(),
        requestId: z.string().uuid(),
        items: z
          .array(
            z.object({
              productId: z.number().int().positive(),
              quantity: z.number().int().min(1).max(10000),
            }),
          )
          .min(1)
          .max(100),
      })
      .parse(req.body);
    const existing = db
      .prepare("SELECT id FROM sales WHERE user_id=? AND request_id=?")
      .get(req.userId, d.requestId);
    if (existing)
      return res.json(salesFor(req.userId).find((s) => s.id === existing.id));
    const id = transaction(db, () => {
      const customer = d.customerId
        ? db
            .prepare("SELECT * FROM customers WHERE id=? AND user_id=?")
            .get(d.customerId, req.userId)
        : null;
      if (d.customerId && !customer) fail(404, "Cliente no encontrado.");
      const merged = new Map();
      for (const item of d.items)
        merged.set(
          item.productId,
          (merged.get(item.productId) || 0) + item.quantity,
        );
      const items = [...merged].map(([productId, quantity]) => {
        const p = db
          .prepare(
            "SELECT * FROM products WHERE id=? AND user_id=? AND active=1",
          )
          .get(productId, req.userId);
        if (!p) fail(404, "Uno de los productos ya no está disponible.");
        if (p.stock < quantity) fail(409, `Stock insuficiente para ${p.name}.`);
        return { ...p, quantity };
      });
      const total = items.reduce(
        (sum, p) => sum + p.price_cents * p.quantity,
        0,
      );
      if (!Number.isSafeInteger(total) || total > 1000000000)
        fail(400, "El total supera el límite permitido.");
      const saleId = Number(
        db
          .prepare(
            "INSERT INTO sales(user_id,customer_id,customer_name,total_cents,status,created_at,request_id) VALUES(?,?,?,?,?,?,?)",
          )
          .run(
            req.userId,
            customer?.id ?? null,
            customer?.name ?? "Cliente general",
            total,
            "pending",
            new Date().toISOString(),
            d.requestId,
          ).lastInsertRowid,
      );
      for (const p of items) {
        db.prepare(
          "INSERT INTO sale_items(sale_id,product_id,name,quantity,price_cents) VALUES(?,?,?,?,?)",
        ).run(saleId, p.id, p.name, p.quantity, p.price_cents);
        db.prepare("UPDATE products SET stock=stock-? WHERE id=?").run(
          p.quantity,
          p.id,
        );
      }
      return saleId;
    });
    res.status(201).json(salesFor(req.userId).find((s) => s.id === id));
  });
  app.post("/api/sales/:id/pay", (req, res) => {
    const d = z
      .object({
        method: z.enum(["Yape", "Plin", "Transferencia", "Efectivo"]),
        reference: z.string().trim().max(80).default(""),
      })
      .parse(req.body);
    if (d.method !== "Efectivo" && !d.reference)
      fail(
        400,
        "Ingresa el número de operación para registrar el pago digital.",
      );
    transaction(db, () => {
      const s = db
        .prepare("SELECT * FROM sales WHERE id=? AND user_id=?")
        .get(req.params.id, req.userId);
      if (!s) fail(404, "Venta no encontrada.");
      if (s.status !== "pending")
        fail(409, "Esta venta ya fue pagada o anulada.");
      db.prepare(
        "INSERT INTO payments(sale_id,method,reference,amount_cents,created_at) VALUES(?,?,?,?,?)",
      ).run(
        s.id,
        d.method,
        d.reference || "Pago en efectivo",
        s.total_cents,
        new Date().toISOString(),
      );
      db.prepare("UPDATE sales SET status='paid' WHERE id=?").run(s.id);
    });
    res.json(salesFor(req.userId).find((s) => s.id === Number(req.params.id)));
  });
  app.post("/api/sales/:id/cancel", (req, res) => {
    transaction(db, () => {
      const s = db
        .prepare("SELECT * FROM sales WHERE id=? AND user_id=?")
        .get(req.params.id, req.userId);
      if (!s) fail(404, "Venta no encontrada.");
      if (s.status !== "pending")
        fail(409, "Solo puedes anular ventas pendientes.");
      for (const i of db
        .prepare("SELECT * FROM sale_items WHERE sale_id=?")
        .all(s.id))
        db.prepare("UPDATE products SET stock=stock+? WHERE id=?").run(
          i.quantity,
          i.product_id,
        );
      db.prepare("UPDATE sales SET status='cancelled' WHERE id=?").run(s.id);
    });
    res.json({ message: "Venta anulada y existencias repuestas." });
  });
  app.get("/api/dashboard", (req, res) => {
    const sales = salesFor(req.userId),
      today = day(new Date());
    const paid = sales.filter((s) => s.status === "paid");
    const series = Array.from({ length: 7 }, (_, i) => {
      const date = day(Date.now() - (6 - i) * 86400000);
      return {
        date,
        totalCents: paid
          .filter((s) => day(s.paidAt) === date)
          .reduce((n, s) => n + s.totalCents, 0),
      };
    });
    res.json({
      todayCents: paid
        .filter((s) => day(s.paidAt) === today)
        .reduce((n, s) => n + s.totalCents, 0),
      paidCents: paid.reduce((n, s) => n + s.totalCents, 0),
      pendingCents: sales
        .filter((s) => s.status === "pending")
        .reduce((n, s) => n + s.totalCents, 0),
      salesCount: sales.filter((s) => s.status !== "cancelled").length,
      lowStock: db
        .prepare(
          "SELECT id,name,stock FROM products WHERE user_id=? AND active=1 AND stock<=min_stock ORDER BY stock",
        )
        .all(req.userId),
      series,
      recentSales: sales.slice(0, 5),
      methods: ["Yape", "Plin", "Transferencia", "Efectivo"].map((method) => ({
        method,
        totalCents: paid
          .filter((s) => s.method === method)
          .reduce((n, s) => n + s.totalCents, 0),
      })),
    });
  });
  app.use((req, res) => res.status(404).json({ error: "Ruta no encontrada." }));
  app.use((err, req, res, next) => {
    if (err instanceof z.ZodError)
      return res
        .status(400)
        .json({
          error: "Revisa los campos del formulario.",
          details: err.issues.map((i) => ({
            field: i.path.join("."),
            message: i.message,
          })),
        });
    if (err.type === "entity.parse.failed")
      return res.status(400).json({ error: "El cuerpo JSON no es válido." });
    if (!err.status) console.error(err);
    res
      .status(err.status || 500)
      .json({
        error: err.status ? err.message : "No se pudo completar la operación.",
      });
  });
  return app;
}
