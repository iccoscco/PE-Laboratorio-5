import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

export function hashPassword(password) {
  const salt = randomBytes(16).toString("hex");
  return `${salt}:${scryptSync(password, salt, 64).toString("hex")}`;
}
export function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(":");
  return timingSafeEqual(
    Buffer.from(hash, "hex"),
    scryptSync(password, salt, 64),
  );
}
export function transaction(db, fn) {
  db.exec("BEGIN IMMEDIATE");
  try {
    const result = fn();
    db.exec("COMMIT");
    return result;
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
}
export function openDatabase(path = "./data/raiz.db", seed = true) {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });
  const db = new DatabaseSync(path);
  db.exec(`PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, business TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', location TEXT NOT NULL DEFAULT 'Lima, Perú');
    CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), name TEXT NOT NULL, category TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents>0), stock INTEGER NOT NULL CHECK(stock>=0), min_stock INTEGER NOT NULL DEFAULT 5, active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), customer_id INTEGER REFERENCES customers(id), customer_name TEXT NOT NULL, total_cents INTEGER NOT NULL CHECK(total_cents>0), status TEXT NOT NULL CHECK(status IN ('pending','paid','cancelled')), created_at TEXT NOT NULL, request_id TEXT NOT NULL, UNIQUE(user_id,request_id));
    CREATE TABLE IF NOT EXISTS sale_items (id INTEGER PRIMARY KEY, sale_id INTEGER NOT NULL REFERENCES sales(id), product_id INTEGER NOT NULL REFERENCES products(id), name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), price_cents INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, sale_id INTEGER UNIQUE NOT NULL REFERENCES sales(id), method TEXT NOT NULL, reference TEXT NOT NULL, amount_cents INTEGER NOT NULL, created_at TEXT NOT NULL);
  `);
  if (
    seed &&
    !db.prepare("SELECT id FROM users WHERE email=?").get("demo@raiz.pe")
  ) {
    transaction(db, () => {
      const user = Number(
        db
          .prepare(
            "INSERT INTO users(name,email,password,business,phone,location) VALUES(?,?,?,?,?,?)",
          )
          .run(
            "María Quispe",
            "demo@raiz.pe",
            hashPassword("Raiz2026!"),
            "Tejidos de mi Tierra",
            "999 123 456",
            "Ayacucho, Perú",
          ).lastInsertRowid,
      );
      const insert = db.prepare(
        "INSERT INTO products(user_id,name,category,price_cents,stock,min_stock) VALUES(?,?,?,?,?,?)",
      );
      for (const p of [
        ["Bolso tejido andino", "Textiles", 8500, 18, 5],
        ["Cerámica de Quinua", "Cerámica", 4500, 4, 5],
        ["Chalina de alpaca", "Textiles", 6500, 12, 5],
        ["Aretes de semillas", "Joyería", 2500, 24, 5],
        ["Retablo ayacuchano", "Decoración", 12000, 3, 4],
        ["Canasta de junco", "Fibras naturales", 3800, 9, 5],
      ])
        insert.run(user, ...p);
      const cust = db.prepare(
        "INSERT INTO customers(user_id,name,phone,email) VALUES(?,?,?,?)",
      );
      cust.run(user, "Lucía Torres", "987 654 321", "lucia@example.com");
      cust.run(user, "Carlos Mendoza", "912 345 678", "carlos@example.com");
      cust.run(user, "Ana Flores", "956 789 123", "");
      const products = db
        .prepare("SELECT * FROM products WHERE user_id=?")
        .all(user);
      for (let i = 0; i < 10; i++) {
        const p = products[i % products.length];
        const quantity = i % 3 === 0 ? 2 : 1;
        const date = new Date(Date.now() - (i % 7) * 86400000).toISOString();
        const customer = db
          .prepare(
            "SELECT * FROM customers WHERE user_id=? ORDER BY id LIMIT 1 OFFSET ?",
          )
          .get(user, i % 3);
        const paid = i % 3 !== 0;
        const id = Number(
          db
            .prepare(
              "INSERT INTO sales(user_id,customer_id,customer_name,total_cents,status,created_at,request_id) VALUES(?,?,?,?,?,?,?)",
            )
            .run(
              user,
              customer.id,
              customer.name,
              p.price_cents * quantity,
              paid ? "paid" : "pending",
              date,
              `seed-${i}`,
            ).lastInsertRowid,
        );
        db.prepare(
          "INSERT INTO sale_items(sale_id,product_id,name,quantity,price_cents) VALUES(?,?,?,?,?)",
        ).run(id, p.id, p.name, quantity, p.price_cents);
        if (paid)
          db.prepare(
            "INSERT INTO payments(sale_id,method,reference,amount_cents,created_at) VALUES(?,?,?,?,?)",
          ).run(
            id,
            ["Yape", "Plin", "Efectivo"][i % 3],
            `DEMO-${1000 + i}`,
            p.price_cents * quantity,
            date,
          );
      }
    });
  }
  return db;
}
