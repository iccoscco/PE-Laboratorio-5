import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { createApp } from "../src/app.js";
import { openDatabase } from "../src/database.js";
const db = openDatabase(":memory:", true);
let server, base, token, otherToken, productId, saleId;
async function api(path, method = "GET", body, auth = token) {
  const r = await fetch(`${base}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(auth ? { Authorization: `Bearer ${auth}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  return { status: r.status, data: r.status === 204 ? null : await r.json() };
}
before(async () => {
  server = createApp(db).listen(0, "127.0.0.1");
  await new Promise((resolve) => server.on("listening", resolve));
  base = `http://127.0.0.1:${server.address().port}/api`;
});
after(async () => {
  await new Promise((resolve) => server.close(resolve));
  db.close();
});
test("rechaza acceso anónimo y contraseñas incorrectas", async () => {
  assert.equal((await api("/products", "GET", undefined, null)).status, 401);
  assert.equal(
    (
      await api(
        "/auth/login",
        "POST",
        { email: "demo@raiz.pe", password: "incorrecta" },
        null,
      )
    ).status,
    401,
  );
  const r = await api(
    "/auth/login",
    "POST",
    { email: "demo@raiz.pe", password: "Raiz2026!" },
    null,
  );
  assert.equal(r.status, 200);
  assert.equal(r.data.user.password, undefined);
  token = r.data.token;
});
test("registro, validación y aislamiento entre negocios", async () => {
  const r = await api(
    "/auth/register",
    "POST",
    {
      name: "Otro usuario",
      business: "Otro taller",
      email: "otro@example.com",
      password: "Clave123!",
    },
    null,
  );
  assert.equal(r.status, 201);
  otherToken = r.data.token;
  assert.deepEqual(
    (await api("/products", "GET", undefined, otherToken)).data,
    [],
  );
  assert.equal(
    (await api("/products", "POST", { name: "Inválido", priceCents: -1 }))
      .status,
    400,
  );
  const p = await api("/products", "POST", {
    name: "Producto de prueba",
    category: "Textiles",
    priceCents: 1299,
    stock: 5,
    minStock: 2,
  });
  assert.equal(p.status, 201);
  productId = p.data.id;
  assert.equal(
    (
      await api(
        `/products/${productId}`,
        "PUT",
        {
          name: "Intruso",
          category: "Otros",
          priceCents: 100,
          stock: 5,
          minStock: 1,
        },
        otherToken,
      )
    ).status,
    404,
  );
});
test("venta calcula precio en servidor, agrupa cantidades y es idempotente", async () => {
  const requestId = randomUUID(),
    body = {
      customerId: null,
      requestId,
      items: [
        { productId, quantity: 1 },
        { productId, quantity: 1 },
      ],
      totalCents: 1,
    };
  const sale = await api("/sales", "POST", body);
  assert.equal(sale.status, 201);
  saleId = sale.data.id;
  assert.equal(sale.data.totalCents, 2598);
  assert.equal(sale.data.items.length, 1);
  assert.equal(
    (await api("/products")).data.find((p) => p.id === productId).stock,
    3,
  );
  const repeat = await api("/sales", "POST", body);
  assert.equal(repeat.data.id, saleId);
  assert.equal(
    (await api("/products")).data.find((p) => p.id === productId).stock,
    3,
  );
});
test("falta de stock revierte toda la operación", async () => {
  const before = (await api("/products")).data;
  const count = (await api("/sales")).data.length;
  const r = await api("/sales", "POST", {
    customerId: null,
    requestId: randomUUID(),
    items: [
      { productId: before.find((p) => p.id !== productId).id, quantity: 1 },
      { productId, quantity: 99999 },
    ],
  });
  assert.equal(r.status, 400);
  const stock = await api("/sales", "POST", {
    customerId: null,
    requestId: randomUUID(),
    items: [{ productId, quantity: 4 }],
  });
  assert.equal(stock.status, 409);
  assert.deepEqual((await api("/products")).data, before);
  assert.equal((await api("/sales")).data.length, count);
});
test("cobro exige referencia y evita duplicados y acceso ajeno", async () => {
  assert.equal(
    (
      await api(
        `/sales/${saleId}/pay`,
        "POST",
        { method: "Yape", reference: "123" },
        otherToken,
      )
    ).status,
    404,
  );
  assert.equal(
    (await api(`/sales/${saleId}/pay`, "POST", { method: "Yape" })).status,
    400,
  );
  const paid = await api(`/sales/${saleId}/pay`, "POST", {
    method: "Yape",
    reference: "TEST-123",
  });
  assert.equal(paid.status, 200);
  assert.equal(paid.data.status, "paid");
  assert.equal(
    (
      await api(`/sales/${saleId}/pay`, "POST", {
        method: "Yape",
        reference: "TEST-123",
      })
    ).status,
    409,
  );
  assert.equal((await api(`/sales/${saleId}/cancel`, "POST")).status, 409);
});
test("anular repone inventario exactamente una vez y conserva historial", async () => {
  const sale = await api("/sales", "POST", {
    customerId: null,
    requestId: randomUUID(),
    items: [{ productId, quantity: 2 }],
  });
  assert.equal(
    (await api("/products")).data.find((p) => p.id === productId).stock,
    1,
  );
  assert.equal(
    (await api(`/sales/${sale.data.id}/cancel`, "POST")).status,
    200,
  );
  assert.equal(
    (await api(`/sales/${sale.data.id}/cancel`, "POST")).status,
    409,
  );
  assert.equal(
    (await api("/products")).data.find((p) => p.id === productId).stock,
    3,
  );
  assert.equal((await api(`/products/${productId}`, "DELETE")).status, 204);
  assert.equal(
    (await api("/sales")).data.find((s) => s.id === saleId).items[0].name,
    "Producto de prueba",
  );
});
test("edita clientes, perfil y revoca la sesión al salir", async () => {
  const c = await api("/customers", "POST", {
    name: "Cliente nuevo",
    phone: "999999999",
    email: "",
  });
  assert.equal(c.status, 201);
  assert.equal(
    (
      await api(`/customers/${c.data.id}`, "PUT", {
        name: "Cliente actualizado",
        phone: "",
        email: "",
      })
    ).status,
    200,
  );
  assert.equal(
    (
      await api("/me", "PATCH", {
        name: "María",
        business: "Taller",
        phone: "",
        location: "Ayacucho",
      })
    ).status,
    200,
  );
  assert.ok((await api("/dashboard")).data.series.length === 7);
  assert.equal((await api("/auth/logout", "POST")).status, 204);
  assert.equal((await api("/me")).status, 401);
});
