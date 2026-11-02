// Browser integration check. Requires Playwright via NODE_PATH.
const { chromium } = require("playwright");
const fs = require("node:fs");
(async () => {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  try {
    await page.goto("http://localhost:8081", { waitUntil: "networkidle" });
    await page
      .getByRole("button", { name: "Entrar a mi negocio", exact: true })
      .click();
    await page.getByText("El pulso de tus ventas").waitFor();
    fs.mkdirSync("docs/evidencias", { recursive: true });
    await page.screenshot({
      path: "docs/evidencias/resumen-web.png",
      fullPage: true,
    });
    await page.getByRole("button", { name: "Productos", exact: true }).click();
    await page
      .getByRole("button", { name: "Agregar producto", exact: true })
      .click();
    const suffix = Date.now();
    await page
      .getByLabel("Nombre del producto", { exact: true })
      .fill(`Prueba UI ${suffix}`);
    await page.getByLabel("Precio de venta en soles").fill("30");
    await page.getByLabel("Stock disponible").fill("5");
    await page
      .getByRole("button", { name: "Guardar producto", exact: true })
      .click();
    await page
      .getByText("Tu producto ya está en el catálogo.", { exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "Ventas y cobros", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Nueva venta", exact: true })
      .click();
    await page
      .getByLabel(`Agregar Prueba UI ${suffix}`, { exact: true })
      .click();
    await page
      .getByRole("button", { name: "Crear venta", exact: true })
      .click();
    await page.getByText("Registrar el cobro", { exact: true }).waitFor();
    await page
      .getByLabel("Número de operación", { exact: true })
      .fill(`UI-${suffix}`);
    await page.getByRole("checkbox").click();
    await page
      .getByRole("button", { name: "Confirmar cobro recibido", exact: true })
      .click();
    await page.getByText("Pago registrado por Yape", { exact: true }).waitFor();
    await page
      .getByRole("button", { name: "Cerrar formulario", exact: true })
      .click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("button", { name: "Mi resumen", exact: true }).click();
    await page.getByText("El pulso de tus ventas").waitFor();
    await page.screenshot({
      path: "docs/evidencias/resumen-movil-web.png",
      fullPage: true,
    });
    await page.getByRole("button", { name: "Productos", exact: true }).click();
    await page.getByLabel("Buscar un producto…").fill(`Prueba UI ${suffix}`);
    await page.getByLabel(`Editar Prueba UI ${suffix}`).click();
    await page
      .getByRole("button", { name: "Retirar del catálogo", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Sí, retirar producto", exact: true })
      .click();
    await page
      .getByText("Producto retirado del catálogo.", { exact: true })
      .waitFor();
    if (errors.length) throw new Error(errors.join("\n"));
    console.log(
      "OK: login, catálogo, venta, cobro, navegación a 390 px y retiro de producto. Sin errores JavaScript.",
    );
  } catch (e) {
    console.log("URL", page.url());
    console.log((await page.locator("body").innerText()).slice(-6000));
    await page.screenshot({
      path: "docs/evidencias/error-web.png",
      fullPage: true,
    });
    throw e;
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
