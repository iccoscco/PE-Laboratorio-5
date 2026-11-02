// Capturas de la aplicación ejecutada para el informe; no altera registros.
const { chromium } = require('playwright');
const fs = require('node:fs');
(async () => {
  fs.mkdirSync('docs/evidencias/movil-blanco-negro', { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if(m.type() === 'error') errors.push(m.text()); });
    const shot = async (name) => {
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: `docs/evidencias/movil-blanco-negro/${name}.png`, animations: 'disabled' });
      console.log(name);
    };
    await page.goto('http://localhost:8081/login', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Entrar a mi negocio', exact: true }).waitFor();
    await page.getByText('Qué bueno verte', {exact:true}).evaluate(el => el.scrollIntoView({block:'start'}));
    await shot('01-acceso');
    await page.getByRole('button', { name: 'Entrar a mi negocio', exact: true }).click();
    await page.getByText('El pulso de tus ventas').waitFor();
    await shot('02-resumen');
    for (const [label, heading, file] of [
      ['Productos', 'Mis productos', '03-productos'],
      ['Clientes', 'Mis clientes', '04-clientes'],
      ['Ventas y cobros', 'Ventas y cobros', '05-ventas'],
    ]) {
      await page.getByRole('button', { name: label, exact: true }).click();
      await page.getByRole('heading', { name: heading, exact: true }).waitFor();
      await shot(file);
    }
    const saleId = await page.evaluate(async () => {
      const token = sessionStorage.getItem('raiz-token');
      const r = await fetch('http://localhost:4000/api/sales', { headers: { Authorization: `Bearer ${token}` } });
      return (await r.json()).find(s => s.status === 'pending')?.id;
    });
    if (!saleId) throw new Error('Se necesita una venta pendiente para mostrar el formulario de cobro.');
    await page.goto(`http://localhost:8081/sales?selected=${saleId}`, { waitUntil: 'networkidle' });
    await page.getByText('Registrar el cobro', { exact: true }).waitFor();
    await page.getByLabel('Número de operación', { exact: true }).fill('DEMO-123456');
    await page.getByLabel('Número de operación', { exact: true }).blur();
    await shot('06-cobro');
    await page.getByRole('button', { name: 'Cerrar formulario', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Mi resumen', exact: true }).click();
    await page.getByText('El pulso de tus ventas').waitFor();
    await page.screenshot({path:'docs/evidencias/resumen-movil-web.png'});
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    if(overflow) throw new Error('Hay desbordamiento horizontal en móvil.');
    if(errors.length) throw new Error(errors.join('\n'));
    console.log('Sin errores de consola ni desbordamiento horizontal a 390 px.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
